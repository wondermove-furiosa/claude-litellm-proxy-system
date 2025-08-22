#!/usr/bin/env python3
"""
코어 마스킹 엔진 패턴 검증 스크립트

MASKING_RULES.md에서 문서화된 56개 패턴이 
실제 CloudPatterns와 MaskingEngine에서 정확히 동작하는지 검증

목적:
1. 모든 56개 패턴의 실제 매칭 동작 확인
2. 충돌 해결 시스템 검증
3. 마스킹/언마스킹 사이클 검증  
4. 우선순위 시스템 정확성 확인
"""

import sys
import os
import json
import time
from typing import Dict, List, Any, Tuple

# 프로젝트 소스 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from claude_litellm_proxy.patterns.cloud_patterns import CloudPatterns
from claude_litellm_proxy.patterns.masking_engine import MaskingEngine
from claude_litellm_proxy.patterns.overlap_detection import OverlapDetectionEngine


def get_comprehensive_test_data() -> Dict[str, Dict[str, Any]]:
    """MASKING_RULES.md에 명시된 전체 56개 패턴 테스트 데이터"""
    
    return {
        # ===== Priority 50-99: 혁신적 추가 패턴 (5개) =====
        "fargate_task": {
            "priority": 50,
            "samples": [
                "arn:aws:ecs:us-east-1:123456789012:task/my-fargate-cluster/1234abcd-12ab-34cd-56ef-1234567890ab",
                "arn:aws:ecs:eu-west-1:987654321098:task/prod-cluster/abcd1234-56ef-78gh-90ij-klmnopqrstuv"
            ],
            "expected_type": "fargate"
        },
        
        "ssm_session": {
            "priority": 60,
            "samples": [
                "s-01234567890abcdef",
                "s-0987654321fedcba0",
                "s-abcdef1234567890a"
            ],
            "expected_type": "ssm_session"
        },
        
        "insights_query": {
            "priority": 75,
            "samples": [
                "12345678-1234-1234-1234-123456789012",
                "abcd1234-ef56-7890-abcd-ef1234567890",
                "87654321-4321-8765-4321-876543218765"
            ],
            "expected_type": "insights"
        },
        
        "apprunner_service": {
            "priority": 85,
            "samples": [
                "arn:aws:apprunner:us-east-1:123456789012:service/my-app-service/8fe1e10304374e7c80684681ea1967",
                "arn:aws:apprunner:eu-west-1:987654321098:service/prod-service/1234567890abcdef1234567890abcd"
            ],
            "expected_type": "apprunner"
        },
        
        "eventbridge_bus": {
            "priority": 95,
            "samples": [
                "arn:aws:events:us-east-1:123456789012:event-bus/my-custom-bus",
                "arn:aws:events:ap-southeast-1:123456789012:event-bus/production-events"
            ],
            "expected_type": "eventbridge"
        },
        
        # ===== Priority 100-199: 구체적 ARN 패턴 (19개) =====
        "lambda_arn": {
            "priority": 100,
            "samples": [
                "arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment",
                "arn:aws:lambda:eu-west-1:987654321098:function:user-authentication"
            ],
            "expected_type": "lambda"
        },
        
        "ecs_task": {
            "priority": 105,
            "samples": [
                "arn:aws:ecs:us-east-1:123456789012:task-definition/web-app:1",
                "arn:aws:ecs:eu-west-1:987654321098:task-definition/api-service:23"
            ],
            "expected_type": "ecs"
        },
        
        "elb_arn": {
            "priority": 110,
            "samples": [
                "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-load-balancer/50dc6c495c0c9188",
                "arn:aws:elasticloadbalancing:eu-west-1:123456789012:loadbalancer/network/prod-nlb/1234567890abcdef"
            ],
            "expected_type": "elb"
        },
        
        "iam_role": {
            "priority": 115,
            "samples": [
                "arn:aws:iam::123456789012:role/EC2-Role",
                "arn:aws:iam::987654321098:role/LambdaExecutionRole"
            ],
            "expected_type": "iam_role"
        },
        
        "iam_user": {
            "priority": 120,
            "samples": [
                "arn:aws:iam::123456789012:user/alice",
                "arn:aws:iam::987654321098:user/service-account"
            ],
            "expected_type": "iam_user"
        },
        
        "sns_topic": {
            "priority": 125,
            "samples": [
                "arn:aws:sns:us-east-1:123456789012:MyTopic",
                "arn:aws:sns:eu-west-1:987654321098:production-alerts"
            ],
            "expected_type": "sns"
        },
        
        "cert_arn": {
            "priority": 130,
            "samples": [
                "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012",
                "arn:aws:acm:eu-west-1:987654321098:certificate/abcdef12-3456-7890-abcd-ef1234567890"
            ],
            "expected_type": "certificate"
        },
        
        "secret_arn": {
            "priority": 135,
            "samples": [
                "arn:aws:secretsmanager:us-east-1:123456789012:secret:MySecret-AbCdEf",
                "arn:aws:secretsmanager:eu-west-1:987654321098:secret:DatabaseCredentials-Xy1Z2a"
            ],
            "expected_type": "secret"
        },
        
        "sqs_queue": {
            "priority": 140,
            "samples": [
                "https://sqs.us-east-1.amazonaws.com/123456789012/MyQueue",
                "https://sqs.eu-west-1.amazonaws.com/987654321098/production-queue"
            ],
            "expected_type": "sqs"
        },
        
        "dynamodb_table": {
            "priority": 145,
            "samples": [
                "arn:aws:dynamodb:us-east-1:123456789012:table/Music",
                "arn:aws:dynamodb:eu-west-1:987654321098:table/UserSessions"
            ],
            "expected_type": "dynamodb"
        },
        
        "kinesis_stream": {
            "priority": 150,
            "samples": [
                "arn:aws:kinesis:us-east-1:123456789012:stream/my-stream",
                "arn:aws:kinesis:eu-west-1:987654321098:stream/analytics-data"
            ],
            "expected_type": "kinesis"
        },
        
        "stepfunctions_arn": {
            "priority": 155,
            "samples": [
                "arn:aws:states:us-east-1:123456789012:stateMachine:HelloWorld",
                "arn:aws:states:eu-west-1:987654321098:stateMachine:DataProcessingPipeline"
            ],
            "expected_type": "stepfunctions"
        },
        
        "batch_job": {
            "priority": 160,
            "samples": [
                "arn:aws:batch:us-east-1:123456789012:job-queue/my-job-queue",
                "arn:aws:batch:eu-west-1:987654321098:job-queue/high-priority-jobs"
            ],
            "expected_type": "batch"
        },
        
        "glue_job": {
            "priority": 165,
            "samples": [
                "arn:aws:glue:us-east-1:123456789012:job/my-glue-job",
                "arn:aws:glue:eu-west-1:987654321098:job/etl-pipeline-job"
            ],
            "expected_type": "glue"
        },
        
        "sagemaker_endpoint": {
            "priority": 170,
            "samples": [
                "arn:aws:sagemaker:us-east-1:123456789012:endpoint/my-endpoint",
                "arn:aws:sagemaker:eu-west-1:987654321098:endpoint/ml-inference-endpoint"
            ],
            "expected_type": "sagemaker"
        },
        
        "athena_workgroup": {
            "priority": 175,
            "samples": [
                "arn:aws:athena:us-east-1:123456789012:workgroup/primary",
                "arn:aws:athena:eu-west-1:987654321098:workgroup/analytics-team"
            ],
            "expected_type": "athena"
        },
        
        "codecommit_repo": {
            "priority": 180,
            "samples": [
                "arn:aws:codecommit:us-east-1:123456789012:repository/MyRepo",
                "arn:aws:codecommit:eu-west-1:987654321098:repository/backend-services"
            ],
            "expected_type": "codecommit"
        },
        
        "log_group": {
            "priority": 185,
            "samples": [
                "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/ProcessPayment",
                "arn:aws:logs:eu-west-1:987654321098:log-group:/aws/apigateway/production"
            ],
            "expected_type": "logs"
        },
        
        "cloudformation_stack": {
            "priority": 190,
            "samples": [
                "arn:aws:cloudformation:us-east-1:123456789012:stack/my-stack/12345678-1234-1234-1234-123456789012",
                "arn:aws:cloudformation:eu-west-1:987654321098:stack/production-infrastructure/abcdef12-3456-7890-abcd-ef1234567890"
            ],
            "expected_type": "cloudformation"
        },
        
        # ===== Priority 200-299: AWS 리소스 ID (14개) =====
        "nat_gateway": {
            "priority": 200,
            "samples": [
                "nat-0123456789abcdef0",
                "nat-abcdef1234567890a"
            ],
            "expected_type": "nat"
        },
        
        "ebs_volume": {
            "priority": 210,
            "samples": [
                "vol-0123456789abcdef0",
                "vol-abcdef1234567890a"
            ],
            "expected_type": "ebs"
        },
        
        "subnet": {
            "priority": 220,
            "samples": [
                "subnet-12345678901234567",
                "subnet-98765432109876543"
            ],
            "expected_type": "subnet"
        },
        
        "vpc": {
            "priority": 230,
            "samples": [
                "vpc-12345678",
                "vpc-abcdef12"
            ],
            "expected_type": "vpc"
        },
        
        "security_group": {
            "priority": 240,
            "samples": [
                "sg-0123456789abcdef0",
                "sg-abcdef1234567890a"
            ],
            "expected_type": "security_group"
        },
        
        "ami_id": {
            "priority": 250,
            "samples": [
                "ami-0123456789abcdef0",
                "ami-abcdef1234567890a"
            ],
            "expected_type": "ami"
        },
        
        "ec2_instance": {
            "priority": 260,
            "samples": [
                "i-0123456789abcdef0",
                "i-abcdef1234567890a"
            ],
            "expected_type": "ec2"
        },
        
        "snapshot": {
            "priority": 270,
            "samples": [
                "snap-0123456789abcdef0",
                "snap-abcdef1234567890a"
            ],
            "expected_type": "snapshot"
        },
        
        "internet_gateway": {
            "priority": 280,
            "samples": [
                "igw-0123456789abcdef0",
                "igw-abcdef1234567890a"
            ],
            "expected_type": "igw"
        },
        
        "efs_filesystem": {
            "priority": 290,
            "samples": [
                "fs-0123456789abcdef0",
                "fs-abcdef1234567890a"
            ],
            "expected_type": "efs"
        },
        
        "rds_instance": {
            "priority": 300,
            "samples": [
                "mydb-instance-1234567",
                "production-db-cluster"
            ],
            "expected_type": "rds"
        },
        
        "elasticache_cluster": {
            "priority": 310,
            "samples": [
                "my-cache-cluster-001",
                "prod-redis-cluster-002"
            ],
            "expected_type": "elasticache"
        },
        
        "redshift_cluster": {
            "priority": 320,
            "samples": [
                "my-redshift-cluster",
                "analytics-cluster-prod"
            ],
            "expected_type": "redshift"
        },
        
        "transit_gateway": {
            "priority": 330,
            "samples": [
                "tgw-0123456789abcdef0",
                "tgw-abcdef1234567890a"
            ],
            "expected_type": "tgw"
        },
        
        # ===== Priority 300-399: 네트워크/API (8개) =====
        "api_gateway": {
            "priority": 340,
            "samples": [
                "https://abcd123456.execute-api.us-east-1.amazonaws.com/prod",
                "https://xyz789abc.execute-api.eu-west-1.amazonaws.com/stage"
            ],
            "expected_type": "api_gateway"
        },
        
        "access_key": {
            "priority": 350,
            "samples": [
                "AKIA1234567890ABCDEF",
                "AKIAXYZ789ABC123DEFG"
            ],
            "expected_type": "access_key"
        },
        
        "route53_zone": {
            "priority": 360,
            "samples": [
                "Z1D633PJN98FT9",
                "Z23ABC4DEF5GH6"
            ],
            "expected_type": "route53"
        },
        
        "kms_key": {
            "priority": 370,
            "samples": [
                "12345678-1234-1234-1234-123456789012",
                "abcdef12-3456-7890-abcd-ef1234567890"
            ],
            "expected_type": "kms"
        },
        
        "ssm_parameter": {
            "priority": 380,
            "samples": [
                "/myapp/database/password",
                "/production/api/secret-key"
            ],
            "expected_type": "ssm_parameter"
        },
        
        "cloudwatch_log": {
            "priority": 390,
            "samples": [
                "/aws/lambda/my-function",
                "/aws/apigateway/production-api"
            ],
            "expected_type": "cloudwatch"
        },
        
        "s3_bucket_logs": {
            "priority": 395,
            "samples": [
                "my-logs-bucket-20231201",
                "application-logs-2024-production"
            ],
            "expected_type": "s3_logs"
        },
        
        "cloudtrail_arn": {
            "priority": 399,
            "samples": [
                "arn:aws:cloudtrail:us-east-1:123456789012:trail/MyTrail",
                "arn:aws:cloudtrail:eu-west-1:987654321098:trail/AuditTrail"
            ],
            "expected_type": "cloudtrail"
        },
        
        # ===== Priority 400-499: IP/광범위 패턴 (4개) =====
        "public_ip": {
            "priority": 460,
            "samples": [
                "203.0.113.12",  # RFC 3849 TEST-NET-3
                "198.51.100.45", # RFC 3849 TEST-NET-2
                "8.8.8.8",       # Google DNS (실제 public)
                "1.1.1.1"        # Cloudflare DNS (실제 public)
            ],
            "expected_type": "public_ip"
        },
        
        "ipv6": {
            "priority": 470,
            "samples": [
                "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
                "2001:db8::1"
            ],
            "expected_type": "ipv6"
        },
        
        "elastic_ip": {
            "priority": 480,
            "samples": [
                "eipalloc-0123456789abcdef0",
                "eipalloc-abcdef1234567890a"
            ],
            "expected_type": "elastic_ip"
        },
        
        "cloudfront": {
            "priority": 490,
            "samples": [
                "d111111abcdef8.cloudfront.net",
                "d222222fedcba9.cloudfront.net"
            ],
            "expected_type": "cloudfront"
        },
        
        # ===== Priority 500-650: Fallback 패턴 (6개) =====
        "arn": {
            "priority": 500,
            "samples": [
                "arn:aws:s3:::my-bucket",
                "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
            ],
            "expected_type": "arn"
        },
        
        "s3_bucket": {
            "priority": 500,
            "samples": [
                "my-production-bucket",
                "company-data-lake-2024"
            ],
            "expected_type": "s3"
        },
        
        "account_id": {
            "priority": 600,
            "samples": [
                "123456789012",
                "987654321098"
            ],
            "expected_type": "account"
        },
        
        "session_token": {
            "priority": 610,
            "samples": [
                "AQoEXAMPLEH4aoAH0gNCAPyJxz4BlCFFxWNE1OPTgk5TthT+FvwqnKwRcOIfrRh3c/LTo6UDdyJwOOvEVPvLXCrrrUtdnniCEXAMPLE",
                "FwoGZXIvYXdzEBQaDGg3S1NnVGZjZ1ZGOyKKASEMAMPLEsessiontokenexample1234567890"
            ],
            "expected_type": "session_token"
        },
        
        "secret_key": {
            "priority": 620,
            "samples": [
                "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "1234567890abcdef1234567890abcdef12345678"
            ],
            "expected_type": "secret_key"
        },
        
        "cloudfront_distribution": {
            "priority": 650,
            "samples": [
                "E1234567890123",
                "EABCDEF123456789"
            ],
            "expected_type": "cloudfront_distribution"
        }
    }


class CorePatternVerification:
    """코어 마스킹 엔진 패턴 검증 클래스"""
    
    def __init__(self):
        """검증 시스템 초기화"""
        print("🔧 CorePatternVerification 초기화 중...")
        
        try:
            self.cloud_patterns = CloudPatterns()
            self.masking_engine = MaskingEngine()
            self.overlap_engine = OverlapDetectionEngine()
            print(f"✅ 시스템 초기화 완료")
        except Exception as e:
            print(f"❌ 초기화 실패: {e}")
            sys.exit(1)
    
    def verify_all_patterns(self) -> Dict[str, Any]:
        """모든 56개 패턴 검증"""
        print(f"\n🎯 [Phase 1] 56개 패턴 개별 검증 시작...")
        
        test_data = get_comprehensive_test_data()
        results = {}
        successful_patterns = 0
        total_samples_tested = 0
        
        for pattern_name, pattern_info in test_data.items():
            print(f"\n🔍 검증 중: {pattern_name} (Priority {pattern_info['priority']})")
            
            pattern_results = {
                "priority": pattern_info["priority"],
                "expected_type": pattern_info["expected_type"],
                "sample_results": [],
                "all_samples_passed": True,
                "detection_rate": 0.0
            }
            
            successful_samples = 0
            
            for i, sample in enumerate(pattern_info["samples"]):
                total_samples_tested += 1
                print(f"  📝 Sample {i+1}: {sample[:50]}...")
                
                try:
                    # CloudPatterns로 직접 매칭 테스트
                    matches = self.cloud_patterns.find_matches(sample)
                    
                    if matches:
                        match = matches[0]  # 첫 번째 매치
                        detected_type = match['pattern_def'].type
                        detected_priority = match['pattern_def'].priority
                        
                        # 타입과 우선순위 검증
                        type_match = detected_type == pattern_info["expected_type"]
                        priority_match = detected_priority == pattern_info["priority"]
                        
                        sample_result = {
                            "sample": sample,
                            "detected": True,
                            "detected_type": detected_type,
                            "expected_type": pattern_info["expected_type"],
                            "type_match": type_match,
                            "detected_priority": detected_priority,
                            "expected_priority": pattern_info["priority"],
                            "priority_match": priority_match,
                            "match_start": match["start"],
                            "match_end": match["end"],
                            "match_length": match["end"] - match["start"]
                        }
                        
                        if type_match and priority_match:
                            successful_samples += 1
                            print(f"    ✅ 성공: {detected_type} (P{detected_priority})")
                        else:
                            print(f"    ❌ 불일치: {detected_type} (P{detected_priority}) != {pattern_info['expected_type']} (P{pattern_info['priority']})")
                            pattern_results["all_samples_passed"] = False
                    
                    else:
                        sample_result = {
                            "sample": sample,
                            "detected": False,
                            "error": "No matches found"
                        }
                        print(f"    ❌ 매칭 실패: No matches found")
                        pattern_results["all_samples_passed"] = False
                    
                    pattern_results["sample_results"].append(sample_result)
                    
                except Exception as e:
                    sample_result = {
                        "sample": sample,
                        "detected": False,
                        "error": str(e)
                    }
                    pattern_results["sample_results"].append(sample_result)
                    print(f"    ❌ 오류: {e}")
                    pattern_results["all_samples_passed"] = False
            
            # 패턴별 성공률 계산
            pattern_results["detection_rate"] = (successful_samples / len(pattern_info["samples"])) * 100
            
            if pattern_results["all_samples_passed"]:
                successful_patterns += 1
                print(f"  🎉 패턴 검증 성공: {pattern_name}")
            else:
                print(f"  💥 패턴 검증 실패: {pattern_name}")
            
            results[pattern_name] = pattern_results
        
        # 전체 성공률 계산
        overall_success_rate = (successful_patterns / len(test_data)) * 100
        
        print(f"\n📊 [Phase 1] 패턴 개별 검증 완료:")
        print(f"   • 성공한 패턴: {successful_patterns}/{len(test_data)} ({overall_success_rate:.1f}%)")
        print(f"   • 테스트한 샘플: {total_samples_tested}개")
        
        return {
            "individual_pattern_results": results,
            "summary": {
                "successful_patterns": successful_patterns,
                "total_patterns": len(test_data),
                "success_rate": overall_success_rate,
                "total_samples_tested": total_samples_tested
            }
        }
    
    def verify_conflict_resolution(self) -> Dict[str, Any]:
        """충돌 해결 시스템 검증"""
        print(f"\n⚔️  [Phase 2] 충돌 해결 시스템 검증 시작...")
        
        # 의도적 충돌 시나리오들
        conflict_scenarios = {
            "lambda_vs_arn": {
                "text": "arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment",
                "expected_winner": "lambda",  # 더 구체적, 높은 우선순위
                "description": "Lambda ARN vs 일반 ARN 충돌"
            },
            
            "account_id_in_arn": {
                "text": "Resource: arn:aws:s3:::my-bucket with account 123456789012",
                "expected_patterns": ["arn", "s3", "account"],
                "description": "ARN 내부 Account ID 충돌"
            },
            
            "vpc_and_subnet": {
                "text": "VPC vpc-12345678 has subnet subnet-12345678901234567",
                "expected_patterns": ["vpc", "subnet"],
                "description": "VPC와 Subnet 동시 존재"
            },
            
            "multiple_ips": {
                "text": "Connect from 203.0.113.12 to 198.51.100.45 via 8.8.8.8",
                "expected_count": 3,
                "description": "다중 Public IP 충돌"
            },
            
            "complex_infrastructure": {
                "text": """
                Deploy to ECS cluster with:
                - Lambda: arn:aws:lambda:us-east-1:123456789012:function:API
                - VPC: vpc-12345678
                - Subnet: subnet-12345678901234567
                - Instance: i-0123456789abcdef0
                - IP: 203.0.113.12
                - Account: 123456789012
                """,
                "min_expected_matches": 5,
                "description": "복합 인프라 시나리오"
            }
        }
        
        results = {}
        successful_scenarios = 0
        
        for scenario_name, scenario_info in conflict_scenarios.items():
            print(f"\n🎭 충돌 시나리오: {scenario_name}")
            print(f"   설명: {scenario_info['description']}")
            
            try:
                # 충돌 해결 포함 매칭
                matches = self.cloud_patterns.find_matches(scenario_info["text"])
                
                scenario_result = {
                    "description": scenario_info["description"],
                    "text": scenario_info["text"],
                    "matches_found": len(matches),
                    "matches": [
                        {
                            "match": match["match"],
                            "type": match["pattern_def"].type,
                            "priority": match["pattern_def"].priority,
                            "start": match["start"],
                            "end": match["end"]
                        }
                        for match in matches
                    ],
                    "success": False
                }
                
                # 시나리오별 성공 조건 검사
                if "expected_winner" in scenario_info:
                    # 특정 패턴이 이겨야 하는 경우
                    if matches and matches[0]["pattern_def"].type == scenario_info["expected_winner"]:
                        scenario_result["success"] = True
                        successful_scenarios += 1
                        print(f"   ✅ 성공: {matches[0]['pattern_def'].type} 패턴이 선택됨")
                    else:
                        winner = matches[0]["pattern_def"].type if matches else "None"
                        print(f"   ❌ 실패: 예상 {scenario_info['expected_winner']} != 실제 {winner}")
                
                elif "expected_count" in scenario_info:
                    # 특정 개수의 매치가 있어야 하는 경우
                    if len(matches) == scenario_info["expected_count"]:
                        scenario_result["success"] = True
                        successful_scenarios += 1
                        print(f"   ✅ 성공: {len(matches)}개 매치 발견")
                    else:
                        print(f"   ❌ 실패: 예상 {scenario_info['expected_count']}개 != 실제 {len(matches)}개")
                
                elif "min_expected_matches" in scenario_info:
                    # 최소 매치 개수가 있어야 하는 경우
                    if len(matches) >= scenario_info["min_expected_matches"]:
                        scenario_result["success"] = True
                        successful_scenarios += 1
                        print(f"   ✅ 성공: {len(matches)}개 매치 발견 (최소 {scenario_info['min_expected_matches']}개)")
                    else:
                        print(f"   ❌ 실패: {len(matches)}개 < 최소 {scenario_info['min_expected_matches']}개")
                
                elif "expected_patterns" in scenario_info:
                    # 특정 패턴들이 모두 있어야 하는 경우
                    found_types = {match["pattern_def"].type for match in matches}
                    expected_types = set(scenario_info["expected_patterns"])
                    
                    if expected_types.issubset(found_types):
                        scenario_result["success"] = True
                        successful_scenarios += 1
                        print(f"   ✅ 성공: 모든 예상 패턴 발견 {expected_types}")
                    else:
                        missing = expected_types - found_types
                        print(f"   ❌ 실패: 누락된 패턴 {missing}")
                
                results[scenario_name] = scenario_result
                
            except Exception as e:
                results[scenario_name] = {
                    "description": scenario_info["description"],
                    "text": scenario_info["text"],
                    "success": False,
                    "error": str(e)
                }
                print(f"   ❌ 오류: {e}")
        
        conflict_success_rate = (successful_scenarios / len(conflict_scenarios)) * 100
        
        print(f"\n📊 [Phase 2] 충돌 해결 검증 완료:")
        print(f"   • 성공한 시나리오: {successful_scenarios}/{len(conflict_scenarios)} ({conflict_success_rate:.1f}%)")
        
        return {
            "conflict_resolution_results": results,
            "summary": {
                "successful_scenarios": successful_scenarios,
                "total_scenarios": len(conflict_scenarios),
                "success_rate": conflict_success_rate
            }
        }
    
    def verify_masking_unmasking_cycle(self) -> Dict[str, Any]:
        """마스킹/언마스킹 사이클 검증"""
        print(f"\n🔄 [Phase 3] 마스킹/언마스킹 사이클 검증 시작...")
        
        # 다양한 복잡도의 테스트 텍스트들
        test_texts = {
            "simple_lambda": "Deploy function arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment",
            
            "multi_resource": """
                Infrastructure setup:
                - Lambda: arn:aws:lambda:us-east-1:123456789012:function:API
                - EC2: i-0123456789abcdef0
                - S3: my-production-bucket
                - VPC: vpc-12345678
                - Account: 123456789012
            """,
            
            "complex_scenario": """
                Production deployment checklist:
                1. Update Lambda function arn:aws:lambda:us-east-1:123456789012:function:UserAuth
                2. Configure ELB arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/api-lb/50dc6c495c0c9188
                3. Verify RDS instance myapp-prod-database is accessible from VPC vpc-12345678
                4. Check CloudWatch logs /aws/lambda/UserAuth for errors
                5. Test API endpoint https://abc123def.execute-api.us-east-1.amazonaws.com/prod
                6. Validate certificates arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012
                7. Monitor from IP 203.0.113.12
            """,
            
            "sensitive_data": """
                Access configuration:
                - Access Key: AKIA1234567890ABCDEF
                - Secret Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
                - Session Token: AQoEXAMPLEH4aoAH0gNCAPyJxz4BlCFFxWNE1OPTgk5TthT+FvwqnKwRcOIfrRh3c/LTo6UDdyJwOOvEVPvLXCrrrUtdnniCEXAMPLE
                - KMS Key: 12345678-1234-1234-1234-123456789012
            """
        }
        
        results = {}
        successful_cycles = 0
        
        for test_name, original_text in test_texts.items():
            print(f"\n🧪 테스트: {test_name}")
            
            try:
                # Step 1: 마스킹
                start_time = time.time()
                masked_text, mapping = self.masking_engine.mask_text(original_text)
                mask_time = time.time() - start_time
                
                # Step 2: 언마스킹
                start_time = time.time()
                unmasked_text = self.masking_engine.unmask_text(masked_text, mapping)
                unmask_time = time.time() - start_time
                
                # 검증
                is_perfect_cycle = (original_text.strip() == unmasked_text.strip())
                resources_masked = len(mapping)
                
                cycle_result = {
                    "original_length": len(original_text),
                    "masked_length": len(masked_text),
                    "resources_masked": resources_masked,
                    "mapping": mapping,
                    "is_perfect_cycle": is_perfect_cycle,
                    "mask_time_ms": round(mask_time * 1000, 2),
                    "unmask_time_ms": round(unmask_time * 1000, 2),
                    "original_sample": original_text[:200] + "..." if len(original_text) > 200 else original_text,
                    "masked_sample": masked_text[:200] + "..." if len(masked_text) > 200 else masked_text
                }
                
                if is_perfect_cycle and resources_masked > 0:
                    successful_cycles += 1
                    print(f"   ✅ 성공: {resources_masked}개 리소스 마스킹/언마스킹 완료")
                    print(f"   ⏱️  성능: 마스킹 {mask_time*1000:.1f}ms, 언마스킹 {unmask_time*1000:.1f}ms")
                else:
                    print(f"   ❌ 실패: Perfect cycle = {is_perfect_cycle}, Resources = {resources_masked}")
                
                results[test_name] = cycle_result
                
            except Exception as e:
                results[test_name] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"   ❌ 오류: {e}")
        
        cycle_success_rate = (successful_cycles / len(test_texts)) * 100
        
        print(f"\n📊 [Phase 3] 마스킹/언마스킹 사이클 검증 완료:")
        print(f"   • 성공한 사이클: {successful_cycles}/{len(test_texts)} ({cycle_success_rate:.1f}%)")
        
        return {
            "masking_cycle_results": results,
            "summary": {
                "successful_cycles": successful_cycles,
                "total_cycles": len(test_texts),
                "success_rate": cycle_success_rate
            }
        }
    
    def generate_comprehensive_report(self, pattern_results: Dict, conflict_results: Dict, cycle_results: Dict) -> Dict[str, Any]:
        """종합 검증 보고서 생성"""
        print(f"\n📋 종합 검증 보고서 생성 중...")
        
        # 전체 성공률 계산
        pattern_success = pattern_results["summary"]["success_rate"]
        conflict_success = conflict_results["summary"]["success_rate"]
        cycle_success = cycle_results["summary"]["success_rate"]
        
        overall_success = (pattern_success + conflict_success + cycle_success) / 3
        
        # 실패한 패턴들 분석
        failed_patterns = [
            name for name, result in pattern_results["individual_pattern_results"].items()
            if not result["all_samples_passed"]
        ]
        
        # 성능 통계
        total_mask_time = sum(
            result.get("mask_time_ms", 0) 
            for result in cycle_results["masking_cycle_results"].values()
            if isinstance(result, dict) and "mask_time_ms" in result
        )
        
        total_unmask_time = sum(
            result.get("unmask_time_ms", 0)
            for result in cycle_results["masking_cycle_results"].values()
            if isinstance(result, dict) and "unmask_time_ms" in result
        )
        
        comprehensive_report = {
            "verification_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "masking_rules_documented": "MASKING_RULES.md",
            "total_patterns_documented": 56,
            
            "verification_summary": {
                "pattern_coverage_success_rate": f"{pattern_success:.1f}%",
                "conflict_resolution_success_rate": f"{conflict_success:.1f}%", 
                "masking_cycle_success_rate": f"{cycle_success:.1f}%",
                "overall_success_rate": f"{overall_success:.1f}%"
            },
            
            "detailed_results": {
                "pattern_verification": pattern_results,
                "conflict_resolution": conflict_results,
                "masking_cycles": cycle_results
            },
            
            "production_readiness": {
                "pattern_coverage": "PASS" if pattern_success >= 90 else "FAIL",
                "conflict_handling": "PASS" if conflict_success >= 80 else "FAIL",
                "masking_reliability": "PASS" if cycle_success >= 95 else "FAIL",
                "overall_status": "PRODUCTION_READY" if overall_success >= 85 else "NEEDS_IMPROVEMENT"
            },
            
            "performance_metrics": {
                "total_masking_time_ms": round(total_mask_time, 2),
                "total_unmasking_time_ms": round(total_unmask_time, 2),
                "average_cycle_time_ms": round((total_mask_time + total_unmask_time) / max(len(cycle_results["masking_cycle_results"]), 1), 2)
            },
            
            "issues_and_recommendations": {
                "failed_patterns": failed_patterns,
                "recommendations": self._generate_recommendations(
                    pattern_success, conflict_success, cycle_success, failed_patterns
                )
            }
        }
        
        return comprehensive_report
    
    def _generate_recommendations(self, pattern_success: float, conflict_success: float, 
                                 cycle_success: float, failed_patterns: List[str]) -> List[str]:
        """검증 결과 기반 권고사항 생성"""
        recommendations = []
        
        if pattern_success < 90:
            recommendations.append(f"패턴 매칭 성공률이 {pattern_success:.1f}%로 낮습니다. 실패한 패턴들을 점검하세요: {', '.join(failed_patterns[:5])}")
        
        if conflict_success < 80:
            recommendations.append("충돌 해결 시스템에 문제가 있습니다. 우선순위 로직을 검토하세요.")
        
        if cycle_success < 95:
            recommendations.append("마스킹/언마스킹 사이클에서 정확도 문제가 발생했습니다. 매핑 로직을 점검하세요.")
        
        if not recommendations:
            recommendations.append("✅ 모든 검증 항목이 기준을 통과했습니다. 프로덕션 배포 준비 완료!")
        
        return recommendations


def main():
    """메인 실행 함수"""
    print("🚀 Claude LiteLLM Proxy - 코어 패턴 검증 시작")
    print("=" * 80)
    print("📖 MASKING_RULES.md에 문서화된 56개 패턴의 실제 동작 검증")
    print("=" * 80)
    
    # 검증 시스템 초기화
    verifier = CorePatternVerification()
    
    # Phase 1: 개별 패턴 검증
    pattern_results = verifier.verify_all_patterns()
    
    # Phase 2: 충돌 해결 검증
    conflict_results = verifier.verify_conflict_resolution()
    
    # Phase 3: 마스킹/언마스킹 사이클 검증
    cycle_results = verifier.verify_masking_unmasking_cycle()
    
    # 종합 보고서 생성
    final_report = verifier.generate_comprehensive_report(
        pattern_results, conflict_results, cycle_results
    )
    
    # 결과 출력
    print("\n" + "=" * 80)
    print("🎉 코어 패턴 검증 완료!")
    print("=" * 80)
    print(f"📊 패턴 매칭: {final_report['verification_summary']['pattern_coverage_success_rate']}")
    print(f"⚔️  충돌 해결: {final_report['verification_summary']['conflict_resolution_success_rate']}")
    print(f"🔄 마스킹 사이클: {final_report['verification_summary']['masking_cycle_success_rate']}")
    print(f"🎯 전체 성공률: {final_report['verification_summary']['overall_success_rate']}")
    print(f"✅ 프로덕션 준비: {final_report['production_readiness']['overall_status']}")
    print("=" * 80)
    
    # JSON 보고서 저장
    report_path = '/Users/wondermove-ca-2/Documents/claude-code-sdk-litellm-proxy/core_pattern_verification_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 상세 보고서 저장됨: {report_path}")
    
    # 권고사항 출력
    if final_report['issues_and_recommendations']['recommendations']:
        print(f"\n💡 권고사항:")
        for i, rec in enumerate(final_report['issues_and_recommendations']['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    return final_report


if __name__ == "__main__":
    main()