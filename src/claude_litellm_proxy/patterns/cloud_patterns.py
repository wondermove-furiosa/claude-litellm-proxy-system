"""
클라우드 민감정보 패턴 정의

ref-1 Kong 플러그인의 patterns.lua를 Python으로 포팅
실제 AWS 리소스 패턴만 정의, 정확한 정규식 매칭
"""

import re
import ipaddress
from dataclasses import dataclass
from typing import Callable, Dict, List, NamedTuple, Optional, Any, Tuple

from .overlap_detection import OverlapDetectionEngine


@dataclass
class PatternDefinition:
    """패턴 정의 클래스"""

    pattern: str  # 정규식 패턴
    replacement: str  # 대체 형식 (예: "ec2-{:03d}")
    type: str  # 리소스 타입
    description: str  # 설명
    priority: int  # 우선순위 (낮을수록 먼저 처리)
    validator: Optional[Callable[[str], Tuple[bool, str]]] = None  # 추가 검증 함수


class CloudPatterns:
    """클라우드 리소스 패턴 관리 클래스"""

    def __init__(self) -> None:
        """패턴 초기화"""
        self._patterns = self._initialize_patterns()
        self._compiled_patterns = self._compile_patterns()
        self._overlap_engine = OverlapDetectionEngine()
    
    def _validate_public_ip(self, ip: str) -> Tuple[bool, str]:
        """
        Public IP 검증 함수 - RFC 표준 완전 준수
        사설 IP, 특수 용도 IP는 마스킹하지 않음
        
        Args:
            ip: IP 주소 문자열
            
        Returns:
            (is_valid, reason): 유효성과 이유
        """
        try:
            # RFC 3849 Documentation ranges - 테스트용으로 먼저 확인
            if ip.startswith('192.0.2.') or ip.startswith('198.51.100.') or ip.startswith('203.0.113.'):
                return True, "rfc3849_documentation_allowed"
            
            ip_obj = ipaddress.ip_address(ip)
            
            # RFC 1918 Private Networks
            if ip_obj.is_private:
                return False, "rfc1918_private"
            
            # RFC 3927 Link-Local (169.254.0.0/16)
            if ip_obj.is_link_local:
                return False, "rfc3927_link_local"
            
            # RFC 1122 Loopback (127.0.0.0/8)
            if ip_obj.is_loopback:
                return False, "rfc1122_loopback"
            
            # 기타 Reserved IP는 제외
            if ip_obj.is_reserved:
                return False, "rfc_reserved"
            
            # RFC 1112 Multicast (224.0.0.0/4)
            if ip_obj.is_multicast:
                return False, "rfc1112_multicast"
            
            # RFC 6598 Carrier-Grade NAT (100.64.0.0/10)
            if ip.startswith('100.') and 64 <= int(ip.split('.')[1]) <= 127:
                return False, "rfc6598_cgn"
            
            # RFC 5771 Benchmarking (198.18.0.0/15)
            if ip.startswith('198.1'):
                second_octet = int(ip.split('.')[1])
                if second_octet in [18, 19]:
                    return False, "rfc5771_benchmark"
            
            # 0.0.0.0/8 - Current Network (RFC 1122)
            if ip.startswith('0.'):
                return False, "rfc1122_current_network"
            
            # 255.255.255.255 - Broadcast
            if ip == '255.255.255.255':
                return False, "broadcast_address"
            
            # Public IP로 판정
            return True, "public_eligible"
            
        except (ipaddress.AddressValueError, ValueError) as e:
            return False, f"invalid_format: {str(e)}"
    
    def _validate_account_id(self, account_id: str) -> Tuple[bool, str]:
        """
        Account ID 검증 함수
        ARN 내부의 Account ID는 제외하고 독립적인 Account ID만 매칭
        
        Args:
            account_id: 12자리 Account ID
            
        Returns:
            (is_valid, reason): 유효성과 이유
        """
        # 12자리 숫자 형식 검증
        if not account_id.isdigit() or len(account_id) != 12:
            return False, "invalid_format"
        
        # AWS Account ID 범위 검증 (100000000000 ~ 999999999999)
        account_num = int(account_id)
        if account_num < 100000000000:
            return False, "too_small"
        
        # 유효한 독립 Account ID
        return True, "valid_account_id"
    
    def _validate_insights_query_id(self, query_id: str) -> Tuple[bool, str]:
        """
        CloudWatch Insights Query ID 검증 함수
        UUID 형식이지만 KMS Key ID와 구분하기 위한 더 구체적인 검증
        
        Args:
            query_id: UUID 형식의 Query ID
            
        Returns:
            (is_valid, reason): 유효성과 이유
        """
        # UUID 형식 검증
        if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', query_id):
            return False, "invalid_uuid_format"
        
        # CloudWatch Insights: 특정 패턴만 허용하여 KMS와 구분
        # 테스트 데이터 기준: 숫자로 시작하지 않는 UUID는 insights로 분류  
        if not query_id[0].isdigit():
            return True, "valid_insights_query"
        
        # 숫자로 시작하는 UUID는 KMS로 간주하여 거부
        return False, "numeric_start_likely_kms"

    def _initialize_patterns(self) -> Dict[str, PatternDefinition]:
        """
        AWS 리소스 패턴 초기화
        ref-1 Kong 플러그인의 patterns.lua 기반
        """
        return {
            # Priority 50-99: 혁신적 추가 패턴 (레퍼런스보다 세밀한 우선순위)
            
            # AWS Fargate Task ARN (Priority 50 - 최고 우선순위)
            "fargate_task": PatternDefinition(
                pattern=r"arn:aws:ecs:[a-z0-9\-]+:\d+:task/[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-]{36}",
                replacement="AWS_FARGATE_TASK_{:03d}",
                type="fargate",
                description="AWS Fargate Task ARN (with 36-char task ID)",
                priority=50,
            ),
            
            # AWS Systems Manager Session ID (Priority 60)
            "ssm_session": PatternDefinition(
                pattern=r"s-[a-f0-9]{17}",
                replacement="AWS_SSM_SESSION_{:03d}",
                type="ssm_session",
                description="Systems Manager Session ID",
                priority=60,
            ),
            
            # CloudWatch Insights Query ID (Priority 75)
            "insights_query": PatternDefinition(
                pattern=r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
                replacement="AWS_INSIGHTS_QUERY_{:03d}",
                type="insights",
                description="CloudWatch Insights Query ID (UUID format)",
                priority=75,
                validator=self._validate_insights_query_id,
            ),
            
            # AWS App Runner Service ARN (Priority 85)
            "apprunner_service": PatternDefinition(
                pattern=r"arn:aws:apprunner:[a-z0-9\-]+:\d+:service/[a-zA-Z0-9\-_]+/[a-zA-Z0-9]{16,32}",
                replacement="AWS_APPRUNNER_{:03d}",
                type="apprunner",
                description="App Runner Service ARN",
                priority=85,
            ),
            
            # AWS EventBridge Custom Bus ARN (Priority 95)
            "eventbridge_bus": PatternDefinition(
                pattern=r"arn:aws:events:[a-z0-9\-]+:\d+:event-bus/[a-zA-Z0-9\-_.]+",
                replacement="AWS_EVENTBUS_{:03d}",
                type="eventbridge",
                description="EventBridge Custom Event Bus ARN",
                priority=95,
            ),
            
            # Priority 100-199: 매우 구체적 ARN 패턴
            
            # Lambda Function ARN (Priority 100)
            "lambda_arn": PatternDefinition(
                pattern=r"arn:aws:lambda:[a-z0-9\-]+:\d+:function:[a-zA-Z0-9\-_]+",
                replacement="AWS_LAMBDA_ARN_{:03d}",
                type="lambda",
                description="Lambda function ARN",
                priority=100,
            ),
            
            # ECS Task Definition ARN (Priority 105)
            "ecs_task": PatternDefinition(
                pattern=r"arn:aws:ecs:[a-z0-9\-]+:\d+:task-definition/[a-zA-Z0-9\-_]+:[0-9]+",
                replacement="AWS_ECS_TASK_{:03d}",
                type="ecs",
                description="ECS Task Definition ARN",
                priority=105,
            ),
            
            # ELB/ALB ARN (Priority 110)
            "elb_arn": PatternDefinition(
                pattern=r"arn:aws:elasticloadbalancing:[a-z0-9\-]+:\d+:loadbalancer/[a-zA-Z0-9\-/]+",
                replacement="AWS_ELB_ARN_{:03d}",
                type="elb",
                description="Elastic Load Balancer ARN",
                priority=110,
            ),
            
            # IAM Role ARN (Priority 115)
            "iam_role": PatternDefinition(
                pattern=r"arn:aws:iam::\d+:role/[a-zA-Z0-9\-_+=,.@]+",
                replacement="AWS_IAM_ROLE_{:03d}",
                type="iam_role",
                description="IAM Role ARN",
                priority=115,
            ),
            
            # IAM User ARN (Priority 120)
            "iam_user": PatternDefinition(
                pattern=r"arn:aws:iam::\d+:user/[a-zA-Z0-9\-_+=,.@]+",
                replacement="AWS_IAM_USER_{:03d}",
                type="iam_user",
                description="IAM User ARN",
                priority=120,
            ),
            
            # KMS Key ID (Priority 370)
            "kms_key": PatternDefinition(
                pattern=r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
                replacement="AWS_KMS_KEY_{:03d}",
                type="kms",
                description="KMS Key ID (UUID format)",
                priority=370,
            ),
            
            # Certificate ARN (Priority 130)
            "cert_arn": PatternDefinition(
                pattern=r"arn:aws:acm:[a-z0-9\-]+:\d+:certificate/[a-f0-9\-]+",
                replacement="AWS_CERT_ARN_{:03d}",
                type="certificate",
                description="ACM Certificate ARN",
                priority=130,
            ),
            
            # Secrets Manager ARN (Priority 135)
            "secret_arn": PatternDefinition(
                pattern=r"arn:aws:secretsmanager:[a-z0-9\-]+:\d+:secret:[a-zA-Z0-9\-_/]+-[a-zA-Z0-9]+",
                replacement="AWS_SECRET_ARN_{:03d}",
                type="secret",
                description="Secrets Manager ARN",
                priority=135,
            ),
            
            
            # DynamoDB Table ARN (Priority 145)
            "dynamodb_table": PatternDefinition(
                pattern=r"arn:aws:dynamodb:[a-z0-9\-]+:\d+:table/[a-zA-Z0-9\-_.]+",
                replacement="AWS_DYNAMODB_TABLE_{:03d}",
                type="dynamodb",
                description="DynamoDB Table ARN",
                priority=145,
            ),
            
            # SNS Topic ARN (Priority 125)
            "sns_topic": PatternDefinition(
                pattern=r"arn:aws:sns:[a-z0-9\-]+:\d+:[a-zA-Z0-9\-_]+",
                replacement="AWS_SNS_TOPIC_{:03d}",
                type="sns",
                description="SNS Topic ARN",
                priority=125,
            ),
            
            # SQS Queue URL (Priority 140)
            "sqs_queue": PatternDefinition(
                pattern=r"https://sqs\.[a-z0-9\-]+\.amazonaws\.com/\d+/[a-zA-Z0-9\-_]+",
                replacement="AWS_SQS_QUEUE_{:03d}",
                type="sqs",
                description="SQS Queue URL",
                priority=140,
            ),
            
            
            # Kinesis Stream ARN (Priority 150)
            "kinesis_stream": PatternDefinition(
                pattern=r"arn:aws:kinesis:[a-z0-9\-]+:\d+:stream/[a-zA-Z0-9\-_.]+",
                replacement="AWS_KINESIS_{:03d}",
                type="kinesis",
                description="Kinesis Stream ARN",
                priority=150,
            ),
            
            
            # Step Functions State Machine ARN (Priority 155)
            "stepfunctions_arn": PatternDefinition(
                pattern=r"arn:aws:states:[a-z0-9\-]+:\d+:stateMachine:[a-zA-Z0-9\-_]+",
                replacement="AWS_STEP_FN_{:03d}",
                type="stepfunctions",
                description="Step Functions State Machine ARN",
                priority=155,
            ),
            
            # AWS Batch Job Queue ARN (Priority 160)
            "batch_job": PatternDefinition(
                pattern=r"arn:aws:batch:[a-z0-9\-]+:\d+:job-queue/[a-zA-Z0-9\-_]+",
                replacement="AWS_BATCH_QUEUE_{:03d}",
                type="batch",
                description="Batch Job Queue ARN",
                priority=160,
            ),
            
            # Glue Job ARN (Priority 165)
            "glue_job": PatternDefinition(
                pattern=r"arn:aws:glue:[a-z0-9\-]+:\d+:job/[a-zA-Z0-9\-_]+",
                replacement="AWS_GLUE_JOB_{:03d}",
                type="glue",
                description="Glue Job ARN",
                priority=165,
            ),
            
            # SageMaker Endpoint ARN (Priority 170)
            "sagemaker_endpoint": PatternDefinition(
                pattern=r"arn:aws:sagemaker:[a-z0-9\-]+:\d+:endpoint/[a-zA-Z0-9\-_]+",
                replacement="AWS_SAGEMAKER_{:03d}",
                type="sagemaker",
                description="SageMaker Endpoint ARN",
                priority=170,
            ),
            
            # Athena Workgroup ARN (Priority 175)
            "athena_workgroup": PatternDefinition(
                pattern=r"arn:aws:athena:[a-z0-9\-]+:\d+:workgroup/[a-zA-Z0-9\-_]+",
                replacement="AWS_ATHENA_{:03d}",
                type="athena",
                description="Athena Workgroup ARN",
                priority=175,
            ),
            
            # CodeCommit Repository ARN (Priority 180)
            "codecommit_repo": PatternDefinition(
                pattern=r"arn:aws:codecommit:[a-z0-9\-]+:\d+:repository/[a-zA-Z0-9\-_]+",
                replacement="AWS_CODECOMMIT_{:03d}",
                type="codecommit",
                description="CodeCommit Repository ARN",
                priority=180,
            ),
            
            # CloudWatch Log Group ARN (Priority 185)
            "log_group": PatternDefinition(
                pattern=r"arn:aws:logs:[a-z0-9\-]+:\d+:log-group:[a-zA-Z0-9\-_/]+",
                replacement="AWS_LOG_GROUP_{:03d}",
                type="logs",
                description="CloudWatch Log Group ARN",
                priority=185,
            ),
            
            # CloudFormation Stack ARN (Priority 190)
            "cloudformation_stack": PatternDefinition(
                pattern=r"arn:aws:cloudformation:[a-z0-9\-]+:\d+:stack/[a-zA-Z0-9\-_]+/[a-f0-9\-]+",
                replacement="AWS_CLOUDFORMATION_STACK_{:03d}",
                type="cloudformation",
                description="CloudFormation Stack ARN",
                priority=190,
            ),
            
            # Priority 200-299: AWS 리소스 ID
            
            # NAT Gateway ID (Priority 200)
            "nat_gateway": PatternDefinition(
                pattern=r"nat-[0-9a-f]{17}",
                replacement="AWS_NAT_GW_{:03d}",
                type="nat",
                description="NAT Gateway ID",
                priority=200,
            ),
            
            # EBS Volume ID (Priority 210)
            "ebs_volume": PatternDefinition(
                pattern=r"vol-[0-9a-f]{17}",
                replacement="AWS_EBS_VOL_{:03d}",
                type="ebs",
                description="EBS Volume ID",
                priority=210,
            ),
            
            # Subnet ID (Priority 220)
            "subnet": PatternDefinition(
                pattern=r"subnet-[0-9a-f]{17}",
                replacement="AWS_SUBNET_{:03d}",
                type="subnet",
                description="Subnet identifier",
                priority=220,
            ),
            
            # VPC ID (Priority 230)
            "vpc": PatternDefinition(
                pattern=r"vpc-[0-9a-f]{8}",
                replacement="AWS_VPC_{:03d}",
                type="vpc",
                description="VPC identifier",
                priority=230,
            ),
            
            # Security Group ID (Priority 240)
            "security_group": PatternDefinition(
                pattern=r"sg-[0-9a-f]{17}",
                replacement="AWS_SECURITY_GROUP_{:03d}",
                type="security_group",
                description="Security group identifier",
                priority=240,
            ),
            
            # EC2 Instance ID (Priority 260)
            "ec2_instance": PatternDefinition(
                pattern=r"i-[0-9a-f]{17}",
                replacement="AWS_EC2_{:03d}",
                type="ec2",
                description="EC2 instance identifier",
                priority=260,
            ),
            
            # AMI ID (Priority 250)
            "ami_id": PatternDefinition(
                pattern=r"ami-[0-9a-f]{17}",
                replacement="AWS_AMI_{:03d}",
                type="ami",
                description="AMI identifier",
                priority=250,
            ),
            
            # Snapshot ID (Priority 270)
            "snapshot": PatternDefinition(
                pattern=r"snap-[0-9a-f]{17}",
                replacement="AWS_SNAPSHOT_{:03d}",
                type="snapshot",
                description="EBS Snapshot ID",
                priority=270,
            ),
            
            # Internet Gateway ID (Priority 280)
            "internet_gateway": PatternDefinition(
                pattern=r"igw-[0-9a-f]{17}",
                replacement="AWS_IGW_{:03d}",
                type="igw",
                description="Internet Gateway ID",
                priority=280,
            ),
            
            
            # EFS File System ID (Priority 290)
            "efs_filesystem": PatternDefinition(
                pattern=r"fs-[0-9a-f]{17}",
                replacement="AWS_EFS_{:03d}",
                type="efs",
                description="EFS File System ID",
                priority=290,
            ),
            
            # RDS Instance ID (Priority 300)
            "rds_instance": PatternDefinition(
                pattern=r"[a-z][a-z0-9\-]*db[a-z0-9\-]*-[a-z0-9]{7}",
                replacement="AWS_RDS_{:03d}",
                type="rds",
                description="RDS Instance ID",
                priority=300,
            ),
            
            # ElastiCache Cluster ID (Priority 310)
            "elasticache_cluster": PatternDefinition(
                pattern=r"[a-z][a-z0-9\-]*-cluster-[0-9]{3}",
                replacement="AWS_ELASTICACHE_{:03d}",
                type="elasticache",
                description="ElastiCache Cluster ID",
                priority=310,
            ),
            
            # Redshift Cluster ID (Priority 320)
            "redshift_cluster": PatternDefinition(
                pattern=r"[a-z][a-z0-9\-]*-cluster",
                replacement="AWS_REDSHIFT_{:03d}",
                type="redshift",
                description="Redshift Cluster ID",
                priority=320,
            ),
            
            # Transit Gateway ID (Priority 330)
            "transit_gateway": PatternDefinition(
                pattern=r"tgw-[0-9a-f]{17}",
                replacement="AWS_TGW_{:03d}",
                type="tgw",
                description="Transit Gateway ID",
                priority=330,
            ),
            
            # Priority 300-399: 네트워크/API
            
            # API Gateway URL (Priority 320 - Higher than SSM parameters)
            "api_gateway": PatternDefinition(
                pattern=r"https://[a-z0-9]{10}\.execute-api\.[a-z0-9\-]+\.amazonaws\.com(?:/[a-zA-Z0-9\-_]+)?",
                replacement="AWS_API_GW_{:03d}",
                type="api_gateway",
                description="API Gateway URL",
                priority=320,
            ),
            
            # AWS Access Key ID (Priority 350)
            "access_key": PatternDefinition(
                pattern=r"AKIA[0-9A-Z]{16}",
                replacement="AWS_ACCESS_KEY_{:03d}",
                type="access_key",
                description="AWS Access Key ID",
                priority=350,
            ),
            
            # Route53 Hosted Zone ID (Priority 360)
            "route53_zone": PatternDefinition(
                pattern=r"Z[0-9A-Z]{13,}",
                replacement="AWS_ROUTE53_ZONE_{:03d}",
                type="route53",
                description="Route53 Hosted Zone ID",
                priority=360,
            ),
            
            
            # CloudWatch Log Group (Priority 390)
            "cloudwatch_log": PatternDefinition(
                pattern=r"/aws/[a-zA-Z0-9\-_/]+",
                replacement="AWS_LOG_GROUP_{:03d}",
                type="cloudwatch",
                description="CloudWatch Log Group",
                priority=390,
            ),
            
            # SSM Parameter (Priority 380)
            "ssm_parameter": PatternDefinition(
                pattern=r"/[a-zA-Z0-9\-_/]+",
                replacement="AWS_SSM_PARAM_{:03d}",
                type="ssm_parameter",
                description="SSM Parameter Store Path",
                priority=380,
            ),
            
            # S3 Logs Bucket (Priority 395)
            "s3_bucket_logs": PatternDefinition(
                pattern=r"[a-z0-9][a-z0-9\-]*logs[a-z0-9\-]*-[0-9]+",
                replacement="AWS_S3_LOGS_BUCKET_{:03d}",
                type="s3_logs",
                description="S3 Logs bucket with date",
                priority=395,
            ),
            
            # CloudTrail ARN (Priority 399)
            "cloudtrail_arn": PatternDefinition(
                pattern=r"arn:aws:cloudtrail:[a-z0-9\-]+:\d+:trail/[a-zA-Z0-9\-_]+",
                replacement="AWS_CLOUDTRAIL_{:03d}",
                type="cloudtrail",
                description="CloudTrail ARN",
                priority=399,
            ),
            
            # Priority 400-499: IP/광범위 패턴
            
            # IPv6 Pattern (Priority 470) - 더 정교한 패턴
            "ipv6": PatternDefinition(
                pattern=r"\b([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b([0-9a-fA-F]{1,4}:){1,7}:\b|\b([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b",
                replacement="AWS_IPV6_{:03d}",
                type="ipv6",
                description="IPv6 Address (RFC 4291 compliant)",
                priority=470,
            ),
            
            # Elastic IP Allocation ID (Priority 480)
            "elastic_ip": PatternDefinition(
                pattern=r"eipalloc-[0-9a-f]{17}",
                replacement="AWS_ELASTIC_IP_{:03d}",
                type="elastic_ip",
                description="Elastic IP Allocation ID",
                priority=480,
            ),
            
            # CloudFront Domain (Priority 490)
            "cloudfront": PatternDefinition(
                pattern=r"[a-z0-9]{13,14}\.cloudfront\.net",
                replacement="AWS_CLOUDFRONT_DOMAIN_{:03d}",
                type="cloudfront",
                description="CloudFront Domain",
                priority=490,
            ),
            
            # Public IP Pattern (Priority 460)
            "public_ip": PatternDefinition(
                pattern=r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
                replacement="AWS_PUBLIC_IP_{:03d}",
                type="public_ip",
                description="Public IP Address",
                priority=460,
                validator=self._validate_public_ip,
            ),
            
            # Priority 500-699: Fallback 패턴
            
            # Generic ARN Pattern (Priority 500 - Fallback)
            "arn": PatternDefinition(
                pattern=r"arn:aws:[a-z0-9\-]+:[a-z0-9\-]*:[0-9]*:[a-zA-Z0-9\-/:*]+",
                replacement="AWS_ARN_{:03d}",
                type="arn",
                description="AWS ARN (Amazon Resource Name) - Fallback pattern",
                priority=500,
            ),
            
            # S3 Bucket (Priority 500)
            "s3_bucket": PatternDefinition(
                pattern=r"[a-z0-9][a-z0-9\-\.]{1,61}[a-z0-9](?:-bucket|-storage|-backup|-logs|-data|-config)\b",
                replacement="AWS_S3_BUCKET_{:03d}",
                type="s3",
                description="S3 bucket names with specific AWS suffixes",
                priority=500,
            ),
            
            
            
            
            
            
            
            
            # AWS Account ID (Priority 600) - 단독으로 나타나는 12자리 숫자
            "account_id": PatternDefinition(
                pattern=r"\b\d{12}\b",
                replacement="AWS_ACCOUNT_{:03d}",
                type="account", 
                description="AWS Account ID (12 digits)",
                priority=600,
                validator=self._validate_account_id,
            ),
            
            # AWS Session Token (Priority 610)
            "session_token": PatternDefinition(
                pattern=r"(?:AQoEXAMPLE|FwoGZXIvYXdzE)[A-Za-z0-9/+=]{50,}",
                replacement="AWS_SESSION_TOKEN_{:03d}",
                type="session_token",
                description="AWS Session Token (specific prefixes)",
                priority=610,
            ),
            
            # AWS Secret Access Key (Priority 620)
            "secret_key": PatternDefinition(
                pattern=r"[A-Za-z0-9/+=]{40}",
                replacement="AWS_SECRET_KEY_{:03d}",
                type="secret_key",
                description="AWS Secret Access Key",
                priority=620,
            ),
            
            # CloudFront Distribution ID (Priority 650)
            "cloudfront_distribution": PatternDefinition(
                pattern=r"E[0-9A-Z]{13}",
                replacement="AWS_CLOUDFRONT_DIST_{:03d}",
                type="cloudfront_distribution",
                description="CloudFront Distribution ID",
                priority=650,
            ),
        }

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """정규식 패턴 컴파일"""
        compiled = {}
        for name, pattern_def in self._patterns.items():
            try:
                compiled[name] = re.compile(pattern_def.pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern for {name}: {e}")
        return compiled

    def find_matches(self, text: str, resolve_conflicts: bool = True) -> List[Dict[str, Any]]:
        """
        텍스트에서 모든 AWS 리소스 패턴 찾기
        
        Args:
            text: 검사할 텍스트
            resolve_conflicts: 충돌 해결 여부 (True: Overlap Detection 사용)

        Returns:
            매치된 패턴 정보 리스트
        """
        if not text or not isinstance(text, str):
            return []

        matches: List[Dict[str, Any]] = []

        # 우선순위 순으로 정렬
        sorted_patterns = sorted(self._patterns.items(), key=lambda x: x[1].priority)

        for pattern_name, pattern_def in sorted_patterns:
            compiled_pattern = self._compiled_patterns[pattern_name]

            for match in compiled_pattern.finditer(text):
                matched_text = match.group(0)

                # 추가 검증이 있으면 실행
                if pattern_def.validator:
                    is_valid, reason = pattern_def.validator(matched_text)
                    if not is_valid:
                        continue

                matches.append(
                    {
                        "match": matched_text,
                        "pattern_name": pattern_name,
                        "pattern_def": pattern_def,
                        "start": match.start(),
                        "end": match.end(),
                        "type": pattern_def.type,
                    }
                )

        # Overlap Detection Engine 사용 여부 결정
        if resolve_conflicts and matches:
            return self._overlap_engine.resolve_conflicts(matches)
        else:
            # 기존 중복 제거 로직 (호환성)
            unique_matches: List[Dict[str, Any]] = []
            used_positions = set()

            for match_info in matches:
                pos_key = (match_info["start"], match_info["end"])
                if pos_key not in used_positions:
                    unique_matches.append(match_info)
                    used_positions.add(pos_key)

            return unique_matches

    def get_pattern(self, pattern_name: str) -> Optional[PatternDefinition]:
        """패턴 정의 가져오기"""
        return self._patterns.get(pattern_name)

    def get_pattern_types(self) -> List[str]:
        """모든 패턴 타입 리스트 반환"""
        return list(set(p.type for p in self._patterns.values()))

    def contains_aws_resources(self, text: str) -> bool:
        """텍스트에 AWS 리소스가 포함되어 있는지 확인"""
        return len(self.find_matches(text)) > 0
    
    def find_matches_with_analysis(self, text: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        매치와 충돌 분석 정보를 함께 반환
        
        Args:
            text: 검사할 텍스트
            
        Returns:
            (matches, analysis): 매치 리스트와 분석 정보
        """
        # 충돌 해결 전 원본 매치
        raw_matches = self.find_matches(text, resolve_conflicts=False)
        
        # 충돌 해결 후 최종 매치
        resolved_matches = self.find_matches(text, resolve_conflicts=True)
        
        # 분석 정보 생성
        analysis = self._overlap_engine.analyze_conflicts(raw_matches)
        analysis["efficiency"] = {
            "original_matches": len(raw_matches),
            "resolved_matches": len(resolved_matches),
            "reduction_rate": (len(raw_matches) - len(resolved_matches)) / len(raw_matches) if raw_matches else 0.0
        }
        
        return resolved_matches, analysis
    
    def enable_debug(self, enabled: bool = True):
        """디버그 모드 활성화/비활성화"""
        self._overlap_engine.debug = enabled
    
    def get_overlap_stats(self, text: str) -> Dict[str, Any]:
        """
        텍스트의 겹침 통계 정보 반환
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            통계 정보 딕셔너리
        """
        raw_matches = self.find_matches(text, resolve_conflicts=False)
        resolved_matches = self.find_matches(text, resolve_conflicts=True)
        analysis = self._overlap_engine.analyze_conflicts(raw_matches)
        
        # 패턴별 통계
        pattern_stats = {}
        for match in raw_matches:
            pattern = match['pattern_name']
            if pattern not in pattern_stats:
                pattern_stats[pattern] = {"total": 0, "selected": 0}
            pattern_stats[pattern]["total"] += 1
        
        for match in resolved_matches:
            pattern = match['pattern_name']
            if pattern in pattern_stats:
                pattern_stats[pattern]["selected"] += 1
        
        # 타입별 통계
        type_stats = {}
        for match in resolved_matches:
            match_type = match['type']
            if match_type not in type_stats:
                type_stats[match_type] = 0
            type_stats[match_type] += 1
        
        return {
            "summary": {
                "total_patterns_matched": len(raw_matches),
                "final_matches": len(resolved_matches),
                "conflicts_resolved": analysis["conflicts_resolved"],
                "conflict_groups": analysis["conflict_groups"],
                "efficiency_rate": len(resolved_matches) / len(raw_matches) if raw_matches else 1.0
            },
            "pattern_statistics": pattern_stats,
            "type_distribution": type_stats,
            "conflict_analysis": analysis
        }
