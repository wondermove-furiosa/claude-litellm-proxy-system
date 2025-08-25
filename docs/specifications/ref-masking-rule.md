# AWS 클라우드 리소스 마스킹/언마스킹 규칙 참조 문서

## 📋 AWS 리소스 마스킹 규칙 요약표 (우선순위 순)

| 우선순위 | AWS 리소스 타입 | 마스킹 대상 패턴 | 마스킹 완료 형식 | 실제 값 예시 |
|---------|----------------|----------------|----------------|-------------|
| **100** | Lambda Function ARN | `arn:aws:lambda:[region]:[account]:function:[name]` | `AWS_LAMBDA_ARN_%03d` | `arn:aws:lambda:us-east-1:123456789012:function:my-function` |
| **105** | ECS Task ARN | `arn:aws:ecs:[region]:[account]:task/[cluster]/[task-id]` | `AWS_ECS_TASK_%03d` | `arn:aws:ecs:us-east-1:123456789012:task/my-cluster/abc123def456` |
| **110** | ELB/ALB ARN | `arn:aws:elasticloadbalancing:[region]:[account]:loadbalancer/[path]` | `AWS_ELB_ARN_%03d` | `arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/1234567890abcdef` |
| **115** | IAM Role ARN | `arn:aws:iam::[account]:role/[role-name]` | `AWS_IAM_ROLE_%03d` | `arn:aws:iam::123456789012:role/MyRole` |
| **120** | IAM User ARN | `arn:aws:iam::[account]:user/[user-name]` | `AWS_IAM_USER_%03d` | `arn:aws:iam::123456789012:user/MyUser` |
| **125** | KMS Key ID | `[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}` | `AWS_KMS_KEY_%03d` | `12345678-1234-1234-1234-123456789012` |
| **130** | ACM Certificate ARN | `arn:aws:acm:[region]:[account]:certificate/[cert-id]` | `AWS_CERT_ARN_%03d` | `arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012` |
| **135** | Secrets Manager ARN | `arn:aws:secretsmanager:[region]:[account]:secret:[name]-[suffix]` | `AWS_SECRET_ARN_%03d` | `arn:aws:secretsmanager:us-east-1:123456789012:secret:MySecret-AbCdEf` |
| **140** | Parameter Store ARN | `arn:aws:ssm:[region]:[account]:parameter/[path]` | `AWS_PARAM_ARN_%03d` | `arn:aws:ssm:us-east-1:123456789012:parameter/myapp/database/password` |
| **145** | CodeCommit Repository ARN | `arn:aws:codecommit:[region]:[account]:[repo-name]` | `AWS_CODECOMMIT_%03d` | `arn:aws:codecommit:us-east-1:123456789012:my-repo` |
| **150** | DynamoDB Table ARN | `arn:aws:dynamodb:[region]:[account]:table/[table-name]` | `AWS_DYNAMODB_TABLE_%03d` | `arn:aws:dynamodb:us-east-1:123456789012:table/MyTable` |
| **155** | SNS Topic ARN | `arn:aws:sns:[region]:[account]:[topic-name]` | `AWS_SNS_TOPIC_%03d` | `arn:aws:sns:us-east-1:123456789012:MyTopic` |
| **160** | SQS Queue URL | `https://sqs.[region].amazonaws.com/[account]/[queue-name]` | `AWS_SQS_QUEUE_%03d` | `https://sqs.us-east-1.amazonaws.com/123456789012/MyQueue` |
| **165** | CloudFormation Stack ID | `arn:aws:cloudformation:[region]:[account]:stack/[name]/[id]` | `AWS_CLOUDFORMATION_STACK_%03d` | `arn:aws:cloudformation:us-east-1:123456789012:stack/MyStack/12345678-1234-1234-1234-123456789012` |
| **170** | Kinesis Stream ARN | `arn:aws:kinesis:[region]:[account]:stream/[stream-name]` | `AWS_KINESIS_%03d` | `arn:aws:kinesis:us-east-1:123456789012:stream/MyStream` |
| **175** | ElasticSearch Domain ARN | `arn:aws:es:[region]:[account]:domain/[domain-name]` | `AWS_ES_DOMAIN_%03d` | `arn:aws:es:us-east-1:123456789012:domain/my-domain` |
| **180** | Step Functions State Machine | `arn:aws:states:[region]:[account]:stateMachine:[name]` | `AWS_STEP_FN_%03d` | `arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine` |
| **185** | AWS Batch Job Queue | `arn:aws:batch:[region]:[account]:job-queue/[queue-name]` | `AWS_BATCH_QUEUE_%03d` | `arn:aws:batch:us-east-1:123456789012:job-queue/MyJobQueue` |
| **190** | Athena Workgroup | `arn:aws:athena:[region]:[account]:workgroup/[workgroup-name]` | `AWS_ATHENA_%03d` | `arn:aws:athena:us-east-1:123456789012:workgroup/MyWorkgroup` |
| **200** | NAT Gateway ID | `nat-[0-9a-f]{17}` | `AWS_NAT_GW_%03d` | `nat-0123456789abcdef0` |
| **210** | EBS Volume ID | `vol-[0-9a-f]{17}` | `AWS_EBS_VOL_%03d` | `vol-0123456789abcdef0` |
| **220** | Subnet ID | `subnet-[0-9a-f]{17}` | `AWS_SUBNET_%03d` | `subnet-0123456789abcdef0` |
| **230** | VPC ID | `vpc-[0-9a-f]{8}` | `AWS_VPC_%03d` | `vpc-12345678` |
| **240** | Security Group ID | `sg-[0-9a-f]{8}` | `AWS_SECURITY_GROUP_%03d` | `sg-12345678` |
| **250** | EC2 Instance ID | `i-[0-9a-f]{17}` | `AWS_EC2_%03d` | `i-0123456789abcdef0` |
| **260** | AMI ID | `ami-[0-9a-f]{8}` | `AWS_AMI_%03d` | `ami-12345678` |
| **270** | EFS File System ID | `fs-[0-9a-f]{8}` | `AWS_EFS_%03d` | `fs-12345678` |
| **280** | Internet Gateway ID | `igw-[0-9a-f]{8}` | `AWS_IGW_%03d` | `igw-12345678` |
| **285** | VPN Connection ID | `vpn-[0-9a-f]{8}` | `AWS_VPN_%03d` | `vpn-12345678` |
| **290** | Transit Gateway ID | `tgw-[0-9a-f]{17}` | `AWS_TGW_%03d` | `tgw-0123456789abcdef0` |
| **295** | EBS Snapshot ID | `snap-[0-9a-f]{17}` | `AWS_SNAPSHOT_%03d` | `snap-0123456789abcdef0` |
| **300** | API Gateway ID | `[a-z0-9]{10}.execute-api.[region].amazonaws.com` | `AWS_API_GW_%03d.execute-api.` | `abcdef1234.execute-api.us-east-1.amazonaws.com` |
| **310** | AWS Access Key ID | `AKIA[0-9A-Z]+` | `AWS_ACCESS_KEY_%03d` | `AKIAIOSFODNN7EXAMPLE` |
| **320** | Route53 Hosted Zone ID | `Z[0-9A-Z]{13,}` | `AWS_ROUTE53_ZONE_%03d` | `Z1234567890ABC` |
| **330** | ECR Repository URI | `[0-9]+.dkr.ecr.[region].amazonaws.com/[repo]` | `AWS_ECR_URI_%03d` | `123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo` |
| **340** | CloudWatch Log Group | `/aws/[service]/[log-group]` | `AWS_LOG_GROUP_%03d` | `/aws/lambda/my-function` |
| **400** | IPv6 Address | `[0-9a-fA-F:]+:+[0-9a-fA-F:]+` | `AWS_IPV6_%03d` | `2001:db8::1` |
| **460** | Public IP Address | `[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+` | `AWS_PUBLIC_IP_%03d` | `203.0.113.1` |
| **500** | S3 Bucket (bucket 패턴) | `[a-z0-9][a-z0-9-]*bucket[a-z0-9-]*` | `AWS_S3_BUCKET_%03d` | `my-app-bucket-prod` |
| **500** | ARN Fallback Pattern | `arn:aws:[service]:[region]:[account]:[resource]` | `AWS_ARN_%03d` | `arn:aws:service:us-east-1:123456789012:resource/example` |
| **510** | S3 Logs Bucket | `[a-z0-9][a-z0-9-]*logs[a-z0-9-]*` | `AWS_S3_LOGS_BUCKET_%03d` | `my-app-logs-2023` |
| **520** | RDS Instance | `[a-z-]*db[a-z-]*` | `AWS_RDS_%03d` | `myapp-db-prod` |
| **530** | ElastiCache Cluster | `[a-z][a-z0-9-]*-[0-9a-z]{5}-[0-9a-z]{3}` | `AWS_ELASTICACHE_%03d` | `myapp-cache-001-abc` |
| **540** | EKS Cluster ARN | `arn:aws:eks:[region]:[account]:cluster/[name]` | `AWS_EKS_CLUSTER_%03d` | `arn:aws:eks:us-east-1:123456789012:cluster/my-cluster` |
| **550** | Redshift Cluster ID | `[a-z][a-z0-9-]*-cluster` | `AWS_REDSHIFT_%03d` | `myapp-cluster` |
| **560** | Glue Job Name | `glue-job-[a-zA-Z0-9-_]+` | `AWS_GLUE_JOB_%03d` | `glue-job-data-processing` |
| **570** | SageMaker Endpoint | `arn:aws:sagemaker:[region]:[account]:endpoint/[name]` | `AWS_SAGEMAKER_%03d` | `arn:aws:sagemaker:us-east-1:123456789012:endpoint/my-endpoint` |
| **600** | AWS Account ID | `\d{12}` | `AWS_ACCOUNT_%03d` | `123456789012` |
| **610** | AWS Session Token | `FwoGZXIvYXdzE[A-Za-z0-9+/=]+` | `AWS_SESSION_TOKEN_%03d` | `FwoGZXIvYXdzEDdaDFn5...` |
| **620** | AWS Secret Access Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` | `AWS_SECRET_KEY_%03d` | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| **650** | CloudFront Distribution ID | `E[0-9A-Z]{13}` | `AWS_CLOUDFRONT_%03d` | `E1234567890ABC` |

---

## 📖 개요

이 문서는 ref-1 프로젝트의 Kong AWS 마스킹 플러그인에서 사용하는 AWS 클라우드 리소스 마스킹/언마스킹 로직을 분석하여 정리한 참조 문서입니다.

### 마스킹 시스템 구조
- **엔진**: Kong Lua 플러그인 기반
- **저장소**: Redis 양방향 매핑 스토어
- **검증**: 패턴별 validator 함수 및 우선순위 기반 처리
- **통합**: 기본 패턴 + 확장 패턴 통합 지원

### 우선순위 체계 설명
- **낮은 숫자 = 높은 우선순위** (priority 필드 기준)
- **100번대**: 서버리스/컨테이너 리소스 (Lambda, ECS, ELB 등)
- **200번대**: 네트워크/인프라 리소스 (VPC, EC2, Subnet 등)
- **300번대**: API/보안 리소스 (API Gateway, Access Key 등)
- **400번대**: IP 주소 (IPv6, Public IP)
- **500번대**: 스토리지/데이터베이스 (S3, RDS, ElastiCache 등)
- **600번대**: 계정/인증 정보 (Account ID, Session Token 등)

---

## 🔍 상세 마스킹 로직

### 🔥 최고 우선순위 리소스 (Priority: 100-199)

최고 우선순위로 처리되는 서버리스 및 컨테이너 관련 리소스들입니다.

#### Lambda Function ARN (Priority: 100)
- **패턴**: `arn:aws:lambda:[a-z0-9-]+:[0-9]+:function:[a-zA-Z0-9-_]+`
- **검증**: 완전한 Lambda ARN 형식 확인
- **보안 중요도**: ⭐⭐⭐⭐⭐

#### ECS Task ARN (Priority: 105)
- **패턴**: `arn:aws:ecs:[a-z0-9-]+:[0-9]+:task/[a-f0-9-]+`
- **검증**: ECS 태스크 ARN 형식 및 UUID 패턴 확인
- **보안 중요도**: ⭐⭐⭐⭐⭐

#### KMS Key ID (Priority: 125)
- **패턴**: UUID 형식 `[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}`
- **검증**: UUID 형식의 KMS 키 ID 확인
- **보안 중요도**: ⭐⭐⭐⭐⭐ (매우 민감한 정보)

### 🌐 네트워크/인프라 리소스 (Priority: 200-299)

#### EC2 Instance ID (Priority: 250)
- **패턴**: `i-[0-9a-f]{17}`
- **검증**: EC2 인스턴스 17자리 헥사 ID 형식 확인
- **보안 중요도**: ⭐⭐⭐⭐

#### VPC ID (Priority: 230)
- **패턴**: `vpc-[0-9a-f]{8}`
- **검증**: VPC 8자리 헥사 ID 형식 확인
- **보안 중요도**: ⭐⭐⭐⭐

### 🔐 보안/API 리소스 (Priority: 300-399)

#### AWS Access Key ID (Priority: 310)
- **패턴**: `AKIA[0-9A-Z]+`
- **검증**: AKIA 접두사로 시작하는 20자 액세스 키 확인
- **보안 중요도**: ⭐⭐⭐⭐⭐ (매우 민감한 정보)

#### API Gateway ID (Priority: 300)
- **패턴**: `[a-z0-9]{10}\.execute-api\.`
- **검증**: API Gateway 실행 엔드포인트 형식, execute-api 컨텍스트 확인
- **보안 중요도**: ⭐⭐⭐

### 🌍 IP 주소 (Priority: 400-499)

#### Public IP Address (Priority: 460)
- **패턴**: `[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+`
- **특별 검증 로직**: 
  - RFC 1918 사설 IP 제외 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
  - AWS 메타데이터 서비스 IP 제외 (169.254.0.0/16)
  - 루프백 주소 제외 (127.0.0.0/8)
  - **공인 IP만 마스킹 대상으로 분류**
- **보안 중요도**: ⭐⭐⭐

### 📊 스토리지/데이터베이스 (Priority: 500-599)

#### S3 Bucket (Priority: 500)
- **패턴**: `[a-z0-9][a-z0-9-]*bucket[a-z0-9-]*`
- **검증**: 'bucket' 키워드 포함, S3 명명 규칙 확인
- **보안 중요도**: ⭐⭐⭐

#### RDS Instance (Priority: 520)
- **패턴**: `[a-z-]*db[a-z-]*`
- **검증**: 'db' 키워드 포함, RDS 명명 패턴 확인
- **보안 중요도**: ⭐⭐⭐⭐

### 🔑 최고 보안 계정/인증 정보 (Priority: 600+)

#### AWS Account ID (Priority: 600)
- **패턴**: `\d{12}`
- **검증**: 정확히 12자리 숫자 확인
- **보안 중요도**: ⭐⭐⭐⭐⭐

#### AWS Secret Access Key (Priority: 620)
- **패턴**: 특정 시크릿 키 패턴
- **검증**: AWS 시크릿 키 형식 확인
- **보안 중요도**: ⭐⭐⭐⭐⭐ (최고 민감 정보)

---

## 🔄 마스킹/언마스킹 처리 로직

### 처리 순서
1. **패턴 초기화**: 기본 패턴 + 확장 패턴 통합
2. **우선순위 정렬**: priority 값 기준 오름차순 정렬
3. **순차적 매칭**: 높은 우선순위부터 패턴 적용
4. **검증 수행**: validator 함수 실행 (해당되는 경우)
5. **매핑 저장**: Redis 양방향 매핑 스토어에 저장

### Redis 매핑 구조
```lua
-- Forward mapping: masked_id -> original_value
"aws_masker:map:AWS_EC2_001" = "i-0123456789abcdef0"

-- Reverse mapping: base64(original_value) -> masked_id  
"aws_masker:rev:aS0wMTIzNDU2Nzg5YWJjZGVmMA==" = "AWS_EC2_001"

-- Counter: resource_type -> next_id
"aws_masker:cnt:ec2" = 1
```

### 특별 검증 로직 예시

#### Public IP 검증자 함수
```lua
function validator(ip)
  local is_non_public, reason = is_non_public_ip(ip)
  if is_non_public then
    return false, reason  -- 사설/특수 IP는 마스킹하지 않음
  end
  return true, "public_eligible"  -- 공인 IP만 마스킹
end
```

### 확장성 지원
- **패턴 통합**: pattern_integrator.lua를 통한 새로운 패턴 추가
- **충돌 처리**: 중복 패턴 자동 감지 및 해결  
- **카테고리별 관리**: Lambda, ECS, RDS 등 서비스별 패턴 그룹화

---

## 📈 성능 및 운영 지표

### 성능 지표
- **처리 시간**: < 100ms (설계 목표)
- **Redis 연결**: Connection Pool 최적화
- **메모리 사용**: Fallback 메모리 스토어 지원

### 통계 수집
```lua
-- 일별 통계 (30일 보관)
"aws_masker:stats:20231201" = {
  total: 1000,
  ec2: 150,
  vpc: 50,
  iam: 200
}
```

---

*이 문서는 ref-1 프로젝트의 Kong AWS 마스킹 플러그인 분석을 통해 작성되었으며, 실제 운영 환경에서 검증된 패턴과 로직을 바탕으로 합니다.*