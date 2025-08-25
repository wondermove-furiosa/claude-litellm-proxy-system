#!/usr/bin/env python3
"""
ref-masking-rule.md 100% 준수 검증 테스트

모든 우선순위, 패턴, 누락 사항을 종합적으로 검증하여 
ref 기준 100% 준수를 확인한다.
"""

import sys
import os
sys.path.append('.')

from src.claude_litellm_proxy.patterns.cloud_patterns import CloudPatterns
from typing import Dict, List, Any, Tuple
import json
import traceback


class RefComplianceValidator:
    """ref-masking-rule.md 준수도 100% 검증기"""
    
    def __init__(self):
        """초기화"""
        self.cloud_patterns = CloudPatterns()
        self.ref_priorities = self._load_ref_priorities()
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "compliance_rate": 0.0,
            "details": {}
        }
    
    def _load_ref_priorities(self) -> Dict[str, Tuple[int, str, str]]:
        """
        ref-masking-rule.md 기준 우선순위 로드
        
        Returns:
            Dict[pattern_name, (priority, masked_format, example)]
        """
        return {
            # Priority 100-199: 최고 우선순위 ARN 패턴
            "lambda_arn": (100, "AWS_LAMBDA_ARN_%03d", "arn:aws:lambda:us-east-1:123456789012:function:my-function"),
            "ecs_task": (105, "AWS_ECS_TASK_%03d", "arn:aws:ecs:us-east-1:123456789012:task/my-cluster/abc123def456"),
            "elb_arn": (110, "AWS_ELB_ARN_%03d", "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/1234567890abcdef"),
            "iam_role": (115, "AWS_IAM_ROLE_%03d", "arn:aws:iam::123456789012:role/MyRole"),
            "iam_user": (120, "AWS_IAM_USER_%03d", "arn:aws:iam::123456789012:user/MyUser"),
            "kms_key": (125, "AWS_KMS_KEY_%03d", "12345678-1234-1234-1234-123456789012"),
            "cert_arn": (130, "AWS_CERT_ARN_%03d", "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"),
            "secret_arn": (135, "AWS_SECRET_ARN_%03d", "arn:aws:secretsmanager:us-east-1:123456789012:secret:MySecret-AbCdEf"),
            "param_store_arn": (140, "AWS_PARAM_ARN_%03d", "arn:aws:ssm:us-east-1:123456789012:parameter/myapp/database/password"),
            "codecommit_repo": (145, "AWS_CODECOMMIT_%03d", "arn:aws:codecommit:us-east-1:123456789012:my-repo"),
            "dynamodb_table": (150, "AWS_DYNAMODB_TABLE_%03d", "arn:aws:dynamodb:us-east-1:123456789012:table/MyTable"),
            "sns_topic": (155, "AWS_SNS_TOPIC_%03d", "arn:aws:sns:us-east-1:123456789012:MyTopic"),
            "sqs_queue": (160, "AWS_SQS_QUEUE_%03d", "https://sqs.us-east-1.amazonaws.com/123456789012/MyQueue"),
            "cloudformation_stack": (165, "AWS_CLOUDFORMATION_STACK_%03d", "arn:aws:cloudformation:us-east-1:123456789012:stack/MyStack/12345678-1234-1234-1234-123456789012"),
            "kinesis_stream": (170, "AWS_KINESIS_%03d", "arn:aws:kinesis:us-east-1:123456789012:stream/MyStream"),
            "elasticsearch_domain": (175, "AWS_ES_DOMAIN_%03d", "arn:aws:es:us-east-1:123456789012:domain/my-domain"),
            "stepfunctions_arn": (180, "AWS_STEP_FN_%03d", "arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine"),
            "batch_job": (185, "AWS_BATCH_QUEUE_%03d", "arn:aws:batch:us-east-1:123456789012:job-queue/MyJobQueue"),
            "athena_workgroup": (190, "AWS_ATHENA_%03d", "arn:aws:athena:us-east-1:123456789012:workgroup/MyWorkgroup"),
            
            # Priority 200-299: 네트워크/인프라 리소스
            "nat_gateway": (200, "AWS_NAT_GW_%03d", "nat-0123456789abcdef0"),
            "ebs_volume": (210, "AWS_EBS_VOL_%03d", "vol-0123456789abcdef0"),
            "subnet": (220, "AWS_SUBNET_%03d", "subnet-0123456789abcdef0"),
            "vpc": (230, "AWS_VPC_%03d", "vpc-12345678"),
            "security_group": (240, "AWS_SECURITY_GROUP_%03d", "sg-12345678"),
            "ec2_instance": (250, "AWS_EC2_%03d", "i-0123456789abcdef0"),
            "ami_id": (260, "AWS_AMI_%03d", "ami-12345678"),
            "efs_filesystem": (270, "AWS_EFS_%03d", "fs-12345678"),
            "internet_gateway": (280, "AWS_IGW_%03d", "igw-12345678"),
            "vpn_connection": (285, "AWS_VPN_%03d", "vpn-12345678"),
            "transit_gateway": (290, "AWS_TGW_%03d", "tgw-0123456789abcdef0"),
            "snapshot": (295, "AWS_SNAPSHOT_%03d", "snap-0123456789abcdef0"),
            
            # Priority 300-399: API/보안 리소스
            "api_gateway": (300, "AWS_API_GW_%03d", "abcdef1234.execute-api.us-east-1.amazonaws.com"),
            "access_key": (310, "AWS_ACCESS_KEY_%03d", "AKIAIOSFODNN7EXAMPLE"),
            "route53_zone": (320, "AWS_ROUTE53_ZONE_%03d", "Z1234567890ABC"),
            "ecr_repo_uri": (330, "AWS_ECR_URI_%03d", "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo"),
            "cloudwatch_log": (340, "AWS_LOG_GROUP_%03d", "/aws/lambda/my-function"),
            
            # Priority 400-499: IP 주소
            "ipv6": (400, "AWS_IPV6_%03d", "2001:db8::1"),
            "public_ip": (460, "AWS_PUBLIC_IP_%03d", "203.0.113.1"),
            
            # Priority 500-599: 스토리지/데이터베이스
            "s3_bucket": (500, "AWS_S3_BUCKET_%03d", "my-app-bucket-prod"),
            "arn": (500, "AWS_ARN_%03d", "arn:aws:service:us-east-1:123456789012:resource/example"),
            "s3_bucket_logs": (510, "AWS_S3_LOGS_BUCKET_%03d", "my-app-logs-2023"),
            "rds_instance": (520, "AWS_RDS_%03d", "myapp-db-prod"),
            "elasticache_cluster": (530, "AWS_ELASTICACHE_%03d", "myapp-cache-001-abc"),
            "eks_cluster": (540, "AWS_EKS_CLUSTER_%03d", "arn:aws:eks:us-east-1:123456789012:cluster/my-cluster"),
            "redshift_cluster": (550, "AWS_REDSHIFT_%03d", "myapp-cluster"),
            "glue_job": (560, "AWS_GLUE_JOB_%03d", "glue-job-data-processing"),
            "sagemaker_endpoint": (570, "AWS_SAGEMAKER_%03d", "arn:aws:sagemaker:us-east-1:123456789012:endpoint/my-endpoint"),
            
            # Priority 600+: 계정/인증 정보
            "account_id": (600, "AWS_ACCOUNT_%03d", "123456789012"),
            "session_token": (610, "AWS_SESSION_TOKEN_%03d", "FwoGZXIvYXdzEDdaDFn5..."),
            "secret_key": (620, "AWS_SECRET_KEY_%03d", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),
            "cloudfront_distribution": (650, "AWS_CLOUDFRONT_%03d", "E1234567890ABC")
        }
    
    def test_priority_compliance(self) -> Dict[str, Any]:
        """우선순위 준수도 검증"""
        print("🎯 우선순위 준수도 검증 중...")
        
        results = {
            "total_patterns": len(self.ref_priorities),
            "matched_patterns": 0,
            "priority_matches": 0,
            "missing_patterns": [],
            "wrong_priorities": [],
            "details": {}
        }
        
        for pattern_name, (expected_priority, expected_format, example) in self.ref_priorities.items():
            self.test_results["total_tests"] += 1
            
            # 패턴이 구현되어 있는지 확인
            pattern_def = self.cloud_patterns.get_pattern(pattern_name)
            if not pattern_def:
                results["missing_patterns"].append({
                    "pattern": pattern_name,
                    "expected_priority": expected_priority,
                    "expected_format": expected_format
                })
                self.test_results["failed_tests"] += 1
                continue
                
            results["matched_patterns"] += 1
            
            # 우선순위 일치 확인
            if pattern_def.priority == expected_priority:
                results["priority_matches"] += 1
                results["details"][pattern_name] = "✅ PASS"
                self.test_results["passed_tests"] += 1
            else:
                results["wrong_priorities"].append({
                    "pattern": pattern_name,
                    "expected": expected_priority,
                    "actual": pattern_def.priority,
                    "diff": pattern_def.priority - expected_priority
                })
                results["details"][pattern_name] = f"❌ FAIL (expected: {expected_priority}, got: {pattern_def.priority})"
                self.test_results["failed_tests"] += 1
        
        # 준수율 계산
        results["compliance_rate"] = (results["priority_matches"] / results["total_patterns"]) * 100
        
        return results
    
    def test_pattern_functionality(self) -> Dict[str, Any]:
        """패턴 기능 검증"""
        print("🔍 패턴 기능 검증 중...")
        
        results = {
            "functional_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": {}
        }
        
        # 각 패턴별 실제 매칭 테스트
        for pattern_name, (priority, format_str, example) in self.ref_priorities.items():
            self.test_results["total_tests"] += 1
            results["functional_tests"] += 1
            
            try:
                # 실제 매칭 테스트
                matches = self.cloud_patterns.find_matches(f"Resource: {example}")
                
                # 해당 패턴이 감지되었는지 확인
                pattern_detected = False
                for match in matches:
                    if match.get('pattern_name') == pattern_name:
                        pattern_detected = True
                        break
                
                if pattern_detected:
                    results["passed_tests"] += 1
                    results["test_details"][pattern_name] = "✅ DETECTED"
                    self.test_results["passed_tests"] += 1
                else:
                    results["failed_tests"] += 1
                    results["test_details"][pattern_name] = f"❌ NOT DETECTED: {example}"
                    self.test_results["failed_tests"] += 1
                    
            except Exception as e:
                results["failed_tests"] += 1
                results["test_details"][pattern_name] = f"💥 ERROR: {str(e)}"
                self.test_results["failed_tests"] += 1
        
        return results
    
    def test_conflict_resolution(self) -> Dict[str, Any]:
        """충돌 해결 검증"""
        print("⚔️ 충돌 해결 검증 중...")
        
        # 충돌이 발생하는 테스트 케이스들
        conflict_cases = [
            {
                "name": "Lambda ARN vs Account ID",
                "text": "arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment",
                "expected_winner": "lambda_arn",
                "expected_priority": 100
            },
            {
                "name": "KMS Key vs Account ID", 
                "text": "12345678-1234-1234-1234-123456789012",
                "expected_winner": "kms_key",
                "expected_priority": 125
            },
            {
                "name": "VPC vs EC2 Instance",
                "text": "Deploy i-0123456789abcdef0 in vpc-12345678",
                "expected_priorities": [230, 250]  # VPC가 더 높은 우선순위
            }
        ]
        
        results = {
            "conflict_tests": len(conflict_cases),
            "passed_conflicts": 0,
            "failed_conflicts": 0,
            "conflict_details": {}
        }
        
        for case in conflict_cases:
            self.test_results["total_tests"] += 1
            
            try:
                # 충돌 해결 전 원본 매치
                raw_matches = self.cloud_patterns.find_matches(case["text"], resolve_conflicts=False)
                
                # 충돌 해결 후 최종 매치
                resolved_matches = self.cloud_patterns.find_matches(case["text"], resolve_conflicts=True)
                
                # 결과 검증
                if "expected_winner" in case:
                    # 특정 패턴이 승리해야 하는 경우
                    winner_found = False
                    for match in resolved_matches:
                        if match.get('pattern_name') == case["expected_winner"]:
                            winner_found = True
                            break
                    
                    if winner_found:
                        results["passed_conflicts"] += 1
                        results["conflict_details"][case["name"]] = "✅ CORRECT WINNER"
                        self.test_results["passed_tests"] += 1
                    else:
                        results["failed_conflicts"] += 1
                        results["conflict_details"][case["name"]] = f"❌ WRONG WINNER"
                        self.test_results["failed_tests"] += 1
                        
                elif "expected_priorities" in case:
                    # 우선순위 순서 확인
                    priorities = [match.get('priority') for match in resolved_matches]
                    priorities.sort()
                    
                    if priorities == sorted(case["expected_priorities"]):
                        results["passed_conflicts"] += 1
                        results["conflict_details"][case["name"]] = "✅ CORRECT ORDER"
                        self.test_results["passed_tests"] += 1
                    else:
                        results["failed_conflicts"] += 1
                        results["conflict_details"][case["name"]] = f"❌ WRONG ORDER: got {priorities}"
                        self.test_results["failed_tests"] += 1
                        
            except Exception as e:
                results["failed_conflicts"] += 1
                results["conflict_details"][case["name"]] = f"💥 ERROR: {str(e)}"
                self.test_results["failed_tests"] += 1
        
        return results
    
    def test_integration_with_masking_system(self) -> Dict[str, Any]:
        """마스킹 시스템 통합 검증"""
        print("🔗 마스킹 시스템 통합 검증 중...")
        
        # 통합 테스트 케이스
        integration_cases = [
            {
                "name": "Simple Lambda Function",
                "input": "Deploy arn:aws:lambda:us-east-1:123456789012:function:SimpleTest",
                "expected_patterns": ["lambda_arn"]
            },
            {
                "name": "Multi-Resource Infrastructure",
                "input": "Connect EC2 i-0123456789abcdef0 in VPC vpc-12345678 using Access Key AKIA1234567890ABCDEF",
                "expected_patterns": ["ec2_instance", "vpc", "access_key"]
            },
            {
                "name": "Security Resources",
                "input": "Encrypt with KMS 12345678-1234-1234-1234-123456789012 and store secret arn:aws:secretsmanager:us-east-1:123456789012:secret:MySecret-AbCdEf",
                "expected_patterns": ["kms_key", "secret_arn"]
            }
        ]
        
        results = {
            "integration_tests": len(integration_cases),
            "passed_integrations": 0,
            "failed_integrations": 0,
            "integration_details": {}
        }
        
        for case in integration_cases:
            self.test_results["total_tests"] += 1
            
            try:
                matches = self.cloud_patterns.find_matches(case["input"])
                detected_patterns = [match.get('pattern_name') for match in matches]
                
                # 모든 예상 패턴이 감지되었는지 확인
                all_detected = all(pattern in detected_patterns for pattern in case["expected_patterns"])
                
                if all_detected:
                    results["passed_integrations"] += 1
                    results["integration_details"][case["name"]] = f"✅ ALL DETECTED: {detected_patterns}"
                    self.test_results["passed_tests"] += 1
                else:
                    missing = [p for p in case["expected_patterns"] if p not in detected_patterns]
                    results["failed_integrations"] += 1
                    results["integration_details"][case["name"]] = f"❌ MISSING: {missing}"
                    self.test_results["failed_tests"] += 1
                    
            except Exception as e:
                results["failed_integrations"] += 1
                results["integration_details"][case["name"]] = f"💥 ERROR: {str(e)}"
                self.test_results["failed_tests"] += 1
        
        return results
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """포괄적 검증 테스트 실행"""
        print("🚀 ref-masking-rule.md 100% 준수 검증 시작!")
        print("=" * 80)
        
        # 개별 테스트 실행
        priority_results = self.test_priority_compliance()
        functionality_results = self.test_pattern_functionality()
        conflict_results = self.test_conflict_resolution()
        integration_results = self.test_integration_with_masking_system()
        
        # 전체 준수율 계산
        if self.test_results["total_tests"] > 0:
            self.test_results["compliance_rate"] = (
                self.test_results["passed_tests"] / self.test_results["total_tests"] * 100
            )
        
        # 종합 결과
        comprehensive_results = {
            "timestamp": "2025-08-25T12:00:00Z",
            "overall_compliance": self.test_results["compliance_rate"],
            "total_tests": self.test_results["total_tests"],
            "passed_tests": self.test_results["passed_tests"],
            "failed_tests": self.test_results["failed_tests"],
            "test_results": {
                "priority_compliance": priority_results,
                "pattern_functionality": functionality_results,
                "conflict_resolution": conflict_results,
                "integration_tests": integration_results
            }
        }
        
        return comprehensive_results
    
    def generate_compliance_report(self, results: Dict[str, Any]) -> str:
        """준수도 보고서 생성"""
        report = []
        report.append("🎯 ref-masking-rule.md 100% 준수 검증 보고서")
        report.append("=" * 80)
        
        # 전체 요약
        report.append(f"\n📊 전체 요약")
        report.append(f"전체 테스트: {results['total_tests']}개")
        report.append(f"통과 테스트: {results['passed_tests']}개")
        report.append(f"실패 테스트: {results['failed_tests']}개")
        report.append(f"전체 준수율: {results['overall_compliance']:.1f}%")
        
        if results['overall_compliance'] >= 100:
            report.append("🎉 **ref 기준 100% 준수 달성!**")
        elif results['overall_compliance'] >= 90:
            report.append("🟢 우수한 준수도 (90%+)")
        elif results['overall_compliance'] >= 75:
            report.append("🟡 양호한 준수도 (75%+)")
        else:
            report.append("🔴 개선 필요 (75% 미만)")
        
        # 세부 결과
        priority_res = results["test_results"]["priority_compliance"]
        report.append(f"\n🎯 우선순위 준수도: {priority_res['compliance_rate']:.1f}%")
        report.append(f"- 매칭 패턴: {priority_res['matched_patterns']}/{priority_res['total_patterns']}")
        report.append(f"- 우선순위 일치: {priority_res['priority_matches']}/{priority_res['total_patterns']}")
        report.append(f"- 누락 패턴: {len(priority_res['missing_patterns'])}개")
        report.append(f"- 우선순위 불일치: {len(priority_res['wrong_priorities'])}개")
        
        if priority_res['missing_patterns']:
            report.append("  🔴 누락된 패턴:")
            for missing in priority_res['missing_patterns'][:5]:  # 상위 5개만
                report.append(f"    - {missing['pattern']} (P{missing['expected_priority']})")
        
        if priority_res['wrong_priorities']:
            report.append("  🔴 우선순위 불일치:")
            for wrong in priority_res['wrong_priorities'][:5]:  # 상위 5개만
                report.append(f"    - {wrong['pattern']}: {wrong['expected']} → {wrong['actual']} (차이: {wrong['diff']})")
        
        func_res = results["test_results"]["pattern_functionality"]
        report.append(f"\n🔍 기능 테스트: {func_res['passed_tests']}/{func_res['functional_tests']} 통과")
        
        conflict_res = results["test_results"]["conflict_resolution"]
        report.append(f"⚔️ 충돌 해결: {conflict_res['passed_conflicts']}/{conflict_res['conflict_tests']} 통과")
        
        integration_res = results["test_results"]["integration_tests"]
        report.append(f"🔗 통합 테스트: {integration_res['passed_integrations']}/{integration_res['integration_tests']} 통과")
        
        return "\\n".join(report)


def main():
    """메인 실행 함수"""
    try:
        validator = RefComplianceValidator()
        results = validator.run_comprehensive_tests()
        
        # 보고서 생성
        report = validator.generate_compliance_report(results)
        print("\n" + report)
        
        # JSON 결과 저장
        with open("ref_compliance_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 결과 저장: ref_compliance_test_results.json")
        
        # 성공/실패 판정
        if results["overall_compliance"] >= 100:
            print("\n🎉 ref-masking-rule.md 100% 준수 달성!")
            return 0
        else:
            print(f"\n❌ 준수율 {results['overall_compliance']:.1f}% - 개선 필요")
            return 1
            
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())