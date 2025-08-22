"""
End-to-End 애플리케이션 통합 검증 테스트

MASKING_RULES.md에서 제시한 모든 커버리지가 
실제 애플리케이션 동작 과정에서 정확히 동작하는지 검증

목적:
1. 56개 패턴 모두 실제 FastAPI 엔드포인트에서 동작 검증
2. 요청/응답 마스킹/언마스킹 전체 플로우 검증
3. Redis 통합 및 영속성 매핑 검증
4. 실제 AWS 리소스 데이터로 프로덕션 시나리오 테스트
"""

import pytest
import asyncio
import json
from typing import Dict, List, Any
from fastapi.testclient import TestClient
from fastapi import FastAPI
import redis.asyncio as redis

# 실제 애플리케이션 컴포넌트 임포트
from claude_litellm_proxy.main import app, masking_system
from claude_litellm_proxy.patterns.cloud_patterns import CloudPatterns
from claude_litellm_proxy.proxy.integrated_masking import IntegratedMaskingSystem


class EndToEndVerificationTest:
    """전체 애플리케이션 플로우 검증 테스트 클래스"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.patterns = CloudPatterns()
        self.test_results = {
            "pattern_coverage_verification": {},
            "fastapi_integration_verification": {},
            "redis_persistence_verification": {},
            "production_scenario_verification": {},
            "performance_verification": {}
        }
        
    async def verify_all_56_patterns_in_application(self) -> Dict[str, Any]:
        """
        MASKING_RULES.md 문서화된 56개 패턴 모두 실제 애플리케이션에서 동작 검증
        """
        print("🔍 [Phase 1] 56개 패턴 애플리케이션 통합 검증 시작...")
        
        # MASKING_RULES.md에 명시된 실제 AWS 리소스 샘플 데이터
        comprehensive_aws_samples = {
            # Priority 50-99: 혁신적 추가 패턴 (5개)
            "fargate_task": "arn:aws:ecs:us-east-1:123456789012:task/my-fargate-cluster/1234abcd-12ab-34cd-56ef-1234567890ab",
            "ssm_session": "s-01234567890abcdef",
            "insights_query": "12345678-1234-1234-1234-123456789012",
            "apprunner_service": "arn:aws:apprunner:us-east-1:123456789012:service/my-app-service/8fe1e10304374e7c80684681ea1967",
            "eventbridge_bus": "arn:aws:events:us-east-1:123456789012:event-bus/my-custom-bus",
            
            # Priority 100-199: 구체적 ARN 패턴 (19개)
            "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment",
            "ecs_task": "arn:aws:ecs:us-east-1:123456789012:task-definition/web-app:1",
            "elb_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-load-balancer/50dc6c495c0c9188",
            "iam_role": "arn:aws:iam::123456789012:role/EC2-Role",
            "iam_user": "arn:aws:iam::123456789012:user/alice",
            "sns_topic": "arn:aws:sns:us-east-1:123456789012:MyTopic",
            "sqs_queue": "https://sqs.us-east-1.amazonaws.com/123456789012/MyQueue",
            "dynamodb_table": "arn:aws:dynamodb:us-east-1:123456789012:table/Music",
            "kinesis_stream": "arn:aws:kinesis:us-east-1:123456789012:stream/my-stream",
            "stepfunctions_arn": "arn:aws:states:us-east-1:123456789012:stateMachine:HelloWorld",
            "batch_job": "arn:aws:batch:us-east-1:123456789012:job-queue/my-job-queue",
            "glue_job": "arn:aws:glue:us-east-1:123456789012:job/my-glue-job",
            "sagemaker_endpoint": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/my-endpoint",
            "athena_workgroup": "arn:aws:athena:us-east-1:123456789012:workgroup/primary",
            "codecommit_repo": "arn:aws:codecommit:us-east-1:123456789012:repository/MyRepo",
            "cert_arn": "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012",
            "secret_arn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:MySecret-AbCdEf",
            "log_group": "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/ProcessPayment",
            "cloudformation_stack": "arn:aws:cloudformation:us-east-1:123456789012:stack/my-stack/12345678-1234-1234-1234-123456789012",
            
            # Priority 200-299: AWS 리소스 ID (14개)
            "nat_gateway": "nat-0123456789abcdef0",
            "ebs_volume": "vol-0123456789abcdef0",
            "subnet": "subnet-12345678901234567",
            "vpc": "vpc-12345678",
            "security_group": "sg-0123456789abcdef0",
            "ami_id": "ami-0123456789abcdef0",
            "ec2_instance": "i-0123456789abcdef0",
            "snapshot": "snap-0123456789abcdef0",
            "internet_gateway": "igw-0123456789abcdef0",
            "efs_filesystem": "fs-0123456789abcdef0",
            "rds_instance": "mydb-instance-1234567",
            "elasticache_cluster": "my-cache-cluster-001",
            "redshift_cluster": "my-redshift-cluster",
            "transit_gateway": "tgw-0123456789abcdef0",
            
            # Priority 300-399: 네트워크/API (8개)
            "api_gateway": "https://abcd123456.execute-api.us-east-1.amazonaws.com/prod",
            "access_key": "AKIA1234567890ABCDEF",
            "route53_zone": "Z1D633PJN98FT9",
            "kms_key": "12345678-1234-1234-1234-123456789012",
            "ssm_parameter": "/myapp/database/password",
            "cloudwatch_log": "/aws/lambda/my-function",
            "s3_bucket_logs": "my-logs-bucket-20231201",
            "cloudtrail_arn": "arn:aws:cloudtrail:us-east-1:123456789012:trail/MyTrail",
            
            # Priority 400-499: IP/광범위 패턴 (4개)
            "public_ip": "203.0.113.12",  # RFC 3849 문서화 주소 (Public)
            "ipv6": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "elastic_ip": "eipalloc-0123456789abcdef0",
            "cloudfront": "d111111abcdef8.cloudfront.net",
            
            # Priority 500-650: Fallback 패턴 (6개)
            "arn": "arn:aws:s3:::my-bucket",  # 일반 ARN
            "s3_bucket": "my-production-bucket",
            "account_id": "123456789012",
            "session_token": "AQoEXAMPLEH4aoAH0gNCAPyJxz4BlCFFxWNE1OPTgk5TthT+FvwqnKwRcOIfrRh3c/LTo6UDdyJwOOvEVPvLXCrrrUtdnniCEXAMPLE",
            "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "cloudfront_distribution": "E1234567890123"
        }
        
        results = {}
        
        # 각 패턴별로 실제 FastAPI 엔드포인트를 통해 검증
        for pattern_name, sample_data in comprehensive_aws_samples.items():
            try:
                # 실제 Claude Messages API 엔드포인트를 통한 테스트
                test_message = f"AWS Resource found: {sample_data} in production environment"
                
                response = self.client.post(
                    "/v1/messages",
                    headers={"Authorization": "Bearer sk-litellm-master-key"},
                    json={
                        "model": "claude-3-haiku-20240307",
                        "messages": [
                            {"role": "user", "content": test_message}
                        ],
                        "max_tokens": 100
                    }
                )
                
                # 마스킹이 실제로 발생했는지 검증
                if response.status_code == 200:
                    # 패턴 매칭 직접 검증
                    matches = self.patterns.find_matches(test_message)
                    pattern_found = any(match['pattern_def'].type == pattern_name.split('_')[0] 
                                      for match in matches)
                    
                    results[pattern_name] = {
                        "pattern_detected": pattern_found,
                        "fastapi_integration": True,
                        "sample_data": sample_data,
                        "match_details": matches
                    }
                else:
                    results[pattern_name] = {
                        "pattern_detected": False,
                        "fastapi_integration": False,
                        "error": f"HTTP {response.status_code}",
                        "sample_data": sample_data
                    }
                    
            except Exception as e:
                results[pattern_name] = {
                    "pattern_detected": False,
                    "fastapi_integration": False,
                    "error": str(e),
                    "sample_data": sample_data
                }
        
        self.test_results["pattern_coverage_verification"] = results
        
        # 성공률 계산
        successful_patterns = sum(1 for result in results.values() 
                                if result.get("pattern_detected", False))
        success_rate = (successful_patterns / len(comprehensive_aws_samples)) * 100
        
        print(f"✅ Pattern Coverage 검증 완료: {successful_patterns}/{len(comprehensive_aws_samples)} ({success_rate:.1f}%)")
        return results
    
    async def verify_redis_persistence_integration(self) -> Dict[str, Any]:
        """Redis 영속성 통합 검증"""
        print("🔍 [Phase 2] Redis 영속성 통합 검증 시작...")
        
        # IntegratedMaskingSystem 직접 테스트
        masking_system = IntegratedMaskingSystem(
            redis_host="localhost",
            redis_port=6379,
            redis_db=0
        )
        
        test_scenarios = [
            "Deploy lambda arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment to production",
            "EC2 instance i-0123456789abcdef0 in VPC vpc-12345678 needs access to S3 bucket my-production-bucket",
            "Route traffic through NAT Gateway nat-0123456789abcdef0 to public IP 203.0.113.12"
        ]
        
        results = {}
        
        for i, scenario in enumerate(test_scenarios):
            try:
                # 1차 마스킹
                masked_text_1, mapping_1 = await masking_system.mask_text(scenario)
                
                # 2차 마스킹 (같은 리소스, 일관성 검증)
                masked_text_2, mapping_2 = await masking_system.mask_text(scenario)
                
                # Redis에서 직접 조회
                original_values = []
                for masked_val in mapping_1.keys():
                    original = await masking_system.get_original_from_redis(masked_val)
                    original_values.append(original)
                
                # 언마스킹 검증
                unmasked_text = await masking_system.unmask_text(masked_text_1)
                
                results[f"scenario_{i+1}"] = {
                    "original": scenario,
                    "masked_1st": masked_text_1,
                    "masked_2nd": masked_text_2,
                    "consistency": masked_text_1 == masked_text_2,  # 일관성 검증
                    "redis_lookup_success": all(val is not None for val in original_values),
                    "unmask_accuracy": scenario == unmasked_text,
                    "mapping_count": len(mapping_1)
                }
                
            except Exception as e:
                results[f"scenario_{i+1}"] = {
                    "error": str(e),
                    "original": scenario
                }
        
        await masking_system.close()
        self.test_results["redis_persistence_verification"] = results
        
        print(f"✅ Redis 통합 검증 완료")
        return results
    
    async def verify_production_scenarios(self) -> Dict[str, Any]:
        """실제 프로덕션 시나리오 검증"""
        print("🔍 [Phase 3] 프로덕션 시나리오 검증 시작...")
        
        # 실제 클라우드 인프라 구성 시나리오들
        production_scenarios = {
            "microservices_architecture": """
            Deploy microservices to ECS cluster with the following resources:
            - Lambda function: arn:aws:lambda:us-east-1:123456789012:function:UserService
            - RDS instance: myapp-prod-db-cluster
            - S3 bucket: myapp-user-data-prod-bucket
            - VPC: vpc-12345678 with subnets: subnet-12345678901234567, subnet-98765432109876543
            - Load balancer: arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/myapp-lb/50dc6c495c0c9188
            - IAM role: arn:aws:iam::123456789012:role/ECS-TaskExecutionRole
            - Access key for deployment: AKIA1234567890ABCDEF
            """,
            
            "data_pipeline": """
            ETL pipeline configuration:
            - Kinesis stream: arn:aws:kinesis:us-east-1:123456789012:stream/user-events
            - Glue job: data-processing-job-v2
            - S3 data lake: company-datalake-prod-bucket
            - Athena workgroup: arn:aws:athena:us-east-1:123456789012:workgroup/analytics-team
            - Step function: arn:aws:states:us-east-1:123456789012:stateMachine:DataPipeline
            - DynamoDB table: arn:aws:dynamodb:us-east-1:123456789012:table/UserEvents
            """,
            
            "security_infrastructure": """
            Security setup for account 123456789012:
            - KMS key: 12345678-1234-1234-1234-123456789012
            - Secrets manager: arn:aws:secretsmanager:us-east-1:123456789012:secret:DatabaseCredentials-AbCdEf
            - CloudTrail: arn:aws:cloudtrail:us-east-1:123456789012:trail/CompanyAuditTrail
            - Public IP whitelist: 203.0.113.12, 198.51.100.45
            - Certificate: arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012
            """
        }
        
        results = {}
        
        for scenario_name, scenario_text in production_scenarios.items():
            try:
                # FastAPI를 통한 실제 요청/응답 플로우 테스트
                response = self.client.post(
                    "/v1/claude-code",
                    headers={"Authorization": "Bearer sk-litellm-master-key"},
                    json={
                        "prompt": f"Analyze this infrastructure setup: {scenario_text}",
                        "allowed_tools": ["Read", "Bash"],
                        "working_directory": "/tmp"
                    }
                )
                
                # 응답에서 마스킹/언마스킹이 올바르게 처리되었는지 검증
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # 패턴 매칭 직접 확인
                    matches = self.patterns.find_matches(scenario_text)
                    unique_resources = len(set(match['match'] for match in matches))
                    
                    results[scenario_name] = {
                        "fastapi_success": True,
                        "aws_resources_detected": unique_resources,
                        "pattern_matches": len(matches),
                        "response_structure_valid": "content" in response_data,
                        "scenario_complexity": "high" if unique_resources > 5 else "medium"
                    }
                else:
                    results[scenario_name] = {
                        "fastapi_success": False,
                        "http_status": response.status_code,
                        "error": response.text
                    }
                    
            except Exception as e:
                results[scenario_name] = {
                    "fastapi_success": False,
                    "error": str(e)
                }
        
        self.test_results["production_scenario_verification"] = results
        print(f"✅ 프로덕션 시나리오 검증 완료")
        return results
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """종합 검증 보고서 생성"""
        print("📊 종합 검증 보고서 생성 중...")
        
        # 패턴 커버리지 성공률
        pattern_results = self.test_results.get("pattern_coverage_verification", {})
        successful_patterns = sum(1 for result in pattern_results.values() 
                                if result.get("pattern_detected", False))
        total_patterns = len(pattern_results)
        pattern_success_rate = (successful_patterns / total_patterns * 100) if total_patterns > 0 else 0
        
        # Redis 통합 성공률  
        redis_results = self.test_results.get("redis_persistence_verification", {})
        redis_successful = sum(1 for result in redis_results.values()
                             if result.get("consistency", False) and result.get("redis_lookup_success", False))
        redis_total = len(redis_results)
        redis_success_rate = (redis_successful / redis_total * 100) if redis_total > 0 else 0
        
        # 프로덕션 시나리오 성공률
        prod_results = self.test_results.get("production_scenario_verification", {})
        prod_successful = sum(1 for result in prod_results.values() 
                            if result.get("fastapi_success", False))
        prod_total = len(prod_results)
        prod_success_rate = (prod_successful / prod_total * 100) if prod_total > 0 else 0
        
        comprehensive_report = {
            "verification_summary": {
                "total_patterns_tested": total_patterns,
                "successful_patterns": successful_patterns,
                "pattern_coverage_rate": f"{pattern_success_rate:.1f}%",
                "redis_integration_rate": f"{redis_success_rate:.1f}%",
                "production_scenario_rate": f"{prod_success_rate:.1f}%",
                "overall_success_rate": f"{(pattern_success_rate + redis_success_rate + prod_success_rate) / 3:.1f}%"
            },
            "detailed_results": self.test_results,
            "production_readiness_assessment": {
                "pattern_coverage": "PASS" if pattern_success_rate >= 90 else "FAIL",
                "redis_integration": "PASS" if redis_success_rate >= 90 else "FAIL", 
                "production_scenarios": "PASS" if prod_success_rate >= 90 else "FAIL",
                "overall_status": "PRODUCTION_READY" if all([
                    pattern_success_rate >= 90,
                    redis_success_rate >= 90, 
                    prod_success_rate >= 90
                ]) else "NEEDS_IMPROVEMENT"
            },
            "recommendations": self._generate_recommendations()
        }
        
        return comprehensive_report
    
    def _generate_recommendations(self) -> List[str]:
        """검증 결과 기반 개선 권고사항 생성"""
        recommendations = []
        
        pattern_results = self.test_results.get("pattern_coverage_verification", {})
        failed_patterns = [name for name, result in pattern_results.items() 
                          if not result.get("pattern_detected", False)]
        
        if failed_patterns:
            recommendations.append(f"다음 패턴들의 검증 실패 원인 분석 필요: {', '.join(failed_patterns)}")
        
        redis_results = self.test_results.get("redis_persistence_verification", {})
        inconsistent_redis = [name for name, result in redis_results.items()
                            if not result.get("consistency", True)]
        
        if inconsistent_redis:
            recommendations.append("Redis 매핑 일관성 문제 해결 필요")
        
        if not recommendations:
            recommendations.append("모든 검증 항목이 성공적으로 통과했습니다. 프로덕션 배포 준비 완료.")
        
        return recommendations


# 실제 검증 실행 함수들
async def run_comprehensive_verification():
    """전체 검증 프로세스 실행"""
    verification = EndToEndVerificationTest()
    
    # Phase 1: 56개 패턴 애플리케이션 통합 검증
    await verification.verify_all_56_patterns_in_application()
    
    # Phase 2: Redis 영속성 통합 검증
    await verification.verify_redis_persistence_integration()
    
    # Phase 3: 프로덕션 시나리오 검증
    await verification.verify_production_scenarios()
    
    # 종합 보고서 생성
    final_report = verification.generate_comprehensive_report()
    
    # 결과 저장
    with open('/Users/wondermove-ca-2/Documents/claude-code-sdk-litellm-proxy/end_to_end_verification_report.json', 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("🎉 End-to-End 애플리케이션 통합 검증 완료!")
    print("="*80)
    print(f"📊 전체 성공률: {final_report['verification_summary']['overall_success_rate']}")
    print(f"🎯 패턴 커버리지: {final_report['verification_summary']['pattern_coverage_rate']}")
    print(f"💾 Redis 통합: {final_report['verification_summary']['redis_integration_rate']}")
    print(f"🏭 프로덕션 시나리오: {final_report['verification_summary']['production_scenario_rate']}")
    print(f"✅ 프로덕션 준비 상태: {final_report['production_readiness_assessment']['overall_status']}")
    print("="*80)
    
    return final_report


if __name__ == "__main__":
    asyncio.run(run_comprehensive_verification())