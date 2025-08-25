#!/usr/bin/env python3
"""
Phase 4: 체계적 테스트 프레임워크
56개 패턴 간 충돌 시나리오 지능적 검증 시스템
"""

import sys
import os
import time
import json
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import itertools

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from claude_litellm_proxy.patterns.cloud_patterns import CloudPatterns


class ComprehensiveTestFramework:
    """56개 패턴의 체계적 충돌 검증 프레임워크"""
    
    def __init__(self):
        self.patterns = CloudPatterns()
        self.all_pattern_names = list(self.patterns._patterns.keys())
        self.conflict_scenarios = []
        self.test_results = {}
        
    def generate_realistic_test_data(self) -> Dict[str, str]:
        """각 패턴별 실제 AWS 형식의 테스트 데이터 생성"""
        return {
            # Priority 50-99: 새 패턴들
            'fargate_task': 'arn:aws:ecs:us-east-1:123456789012:task/my-cluster/a1b2c3d4-e5f6-7890-abcd-ef1234567890',
            'ssm_session': 'arn:aws:ssm:us-east-1:123456789012:session/user-12345678901ab',
            'insights_query': 'a1234567-89ab-cdef-0123-456789abcdef',
            'apprunner_service': 'arn:aws:apprunner:us-east-1:123456789012:service/web-app/fedcba0987654321fedcba0987654321',
            'eventbridge_bus': 'arn:aws:events:us-east-1:123456789012:event-bus/custom-business-bus',
            
            # Priority 100-199: ARN 패턴들
            'lambda_arn': 'arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment',
            'ecs_task': 'arn:aws:ecs:us-east-1:123456789012:task/a1b2c3d4-e5f6-7890',
            'elb_arn': 'arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-lb/1234567890abcdef',
            'iam_role': 'arn:aws:iam::123456789012:role/MyServiceRole',
            'iam_user': 'arn:aws:iam::123456789012:user/alice',
            'kms_key': 'f1234567-89ab-cdef-0123-456789abcdef',
            'cert_arn': 'arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012',
            'secret_arn': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:MySecret-AbCdEf',
            'parameter_arn': 'arn:aws:ssm:us-east-1:123456789012:parameter/myapp/config',
            'codecommit': 'arn:aws:codecommit:us-east-1:123456789012:MyRepository',
            'dynamodb_table': 'arn:aws:dynamodb:us-east-1:123456789012:table/Users',
            'sns_topic': 'arn:aws:sns:us-east-1:123456789012:MyTopic',
            'sqs_queue': 'https://sqs.us-east-1.amazonaws.com/123456789012/MyQueue',
            'stack_id': 'arn:aws:cloudformation:us-east-1:123456789012:stack/MyStack/1a2b3c4d-5e6f-7890-abcd-ef1234567890',
            'kinesis': 'arn:aws:kinesis:us-east-1:123456789012:stream/MyStream',
            'elasticsearch': 'arn:aws:es:us-east-1:123456789012:domain/my-domain',
            'stepfunctions': 'arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine',
            'batch_queue': 'arn:aws:batch:us-east-1:123456789012:job-queue/MyJobQueue',
            'athena': 'arn:aws:athena:us-east-1:123456789012:workgroup/primary',
            
            # Priority 200-299: 리소스 ID들
            'nat_gateway': 'nat-1234567890abcdef0',
            'ebs_volume': 'vol-1234567890abcdef0',
            'subnet': 'subnet-1234567890abcdef0',
            'vpc': 'vpc-12345678',
            'security_group': 'sg-12345678',
            'ec2_instance': 'i-1234567890abcdef0',
            'ami': 'ami-12345678',
            'efs_id': 'fs-12345678',
            'igw': 'igw-12345678',
            'vpn': 'vpn-12345678',
            'tgw': 'tgw-1234567890abcdef0',
            'snapshot': 'snap-1234567890abcdef0',
            
            # Priority 300-399: 네트워크/API
            'api_gateway': 'abcdef1234.execute-api.us-east-1.amazonaws.com',
            'access_key': 'AKIA1234567890ABCDEF',
            'route53_zone': 'Z1234567890ABC',
            'ecr_uri': '123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo',
            'log_group': '/aws/lambda/my-function',
            
            # Priority 400+: IP 및 기타
            'ipv6': '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
            'public_ip': '8.8.8.8',
            'arn': 'arn:aws:s3:::my-bucket',  # Generic ARN
            's3_bucket': 'my-data-bucket',
            's3_logs_bucket': 'my-app-logs',
            'rds_instance': 'my-prod-db',
            'elasticache': 'my-cache-abc12-def',
            'eks_cluster': 'arn:aws:eks:us-east-1:123456789012:cluster/my-cluster',
            'redshift': 'my-redshift-cluster',
            'glue_job': 'glue-job-my-etl',
            'sagemaker': 'arn:aws:sagemaker:us-east-1:123456789012:endpoint/my-endpoint',
            'account_id': '123456789012',
            'session_token': 'FwoGZXIvYXdzEDMaDG9uQ2FsbA1234567890',
            'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'cloudfront': 'E1234567890ABC'
        }
    
    def identify_potential_conflicts(self) -> List[Tuple[str, str, str]]:
        """충돌 가능성이 높은 패턴 조합 식별"""
        conflicts = []
        
        # 1. ARN 패턴들 간의 충돌 (Generic ARN vs 구체적 ARN들)
        arn_patterns = [name for name, pattern in self.patterns._patterns.items() 
                       if 'arn:aws:' in pattern.pattern]
        
        for arn_pattern in arn_patterns:
            if arn_pattern != 'arn':  # Generic ARN 제외
                conflicts.append((arn_pattern, 'arn', 'arn_vs_specific'))
        
        # 2. UUID 형식 패턴들 간의 충돌
        uuid_patterns = ['kms_key', 'insights_query']
        for p1, p2 in itertools.combinations(uuid_patterns, 2):
            conflicts.append((p1, p2, 'uuid_format'))
        
        # 3. Account ID와 다른 패턴들의 포함 관계
        patterns_with_account = [name for name, pattern in self.patterns._patterns.items()
                               if r'\d+' in pattern.pattern or '123456789012' in self.generate_realistic_test_data().get(name, '')]
        
        for pattern_name in patterns_with_account[:10]:  # 상위 10개만 테스트
            if pattern_name != 'account_id':
                conflicts.append((pattern_name, 'account_id', 'account_inclusion'))
        
        # 4. 길이가 유사한 ID 패턴들
        similar_length_groups = [
            ['vpc', 'security_group', 'ami', 'efs_id', 'igw', 'vpn'],  # 8자리
            ['ec2_instance', 'ebs_volume', 'subnet', 'nat_gateway', 'tgw', 'snapshot'],  # 17자리
        ]
        
        for group in similar_length_groups:
            for p1, p2 in itertools.combinations(group, 2):
                conflicts.append((p1, p2, 'similar_length'))
        
        # 5. 문자열 포함 관계
        inclusion_pairs = [
            ('s3_bucket', 's3_logs_bucket', 'string_inclusion'),
            ('rds_instance', 'elb_arn', 'substring_match'),
            ('lambda_arn', 'lambda', 'name_similarity')
        ]
        
        conflicts.extend(inclusion_pairs)
        
        return conflicts
    
    def create_conflict_test_scenarios(self, conflicts: List[Tuple[str, str, str]]) -> List[Dict]:
        """충돌 시나리오별 테스트 케이스 생성"""
        test_data = self.generate_realistic_test_data()
        scenarios = []
        
        for pattern1, pattern2, conflict_type in conflicts:
            if pattern1 in test_data and pattern2 in test_data:
                # 두 패턴이 모두 포함된 텍스트 생성
                text = f"Resource A: {test_data[pattern1]} and Resource B: {test_data[pattern2]}"
                
                scenarios.append({
                    'scenario_id': len(scenarios) + 1,
                    'pattern1': pattern1,
                    'pattern2': pattern2,
                    'conflict_type': conflict_type,
                    'test_text': text,
                    'expected_patterns': [pattern1, pattern2]
                })
                
                # Overlap 시나리오: 두 패턴이 겹치는 경우
                if conflict_type in ['arn_vs_specific', 'account_inclusion']:
                    overlap_text = test_data[pattern1]  # 하나의 텍스트에서 두 패턴 모두 매칭 가능
                    scenarios.append({
                        'scenario_id': len(scenarios) + 1,
                        'pattern1': pattern1,
                        'pattern2': pattern2,
                        'conflict_type': f'{conflict_type}_overlap',
                        'test_text': overlap_text,
                        'expected_winner': pattern1 if self.patterns._patterns[pattern1].priority < self.patterns._patterns[pattern2].priority else pattern2
                    })
        
        return scenarios
    
    def run_comprehensive_tests(self) -> Dict:
        """포괄적 테스트 실행"""
        print("🚀 Comprehensive Test Framework - Phase 4")
        print("=" * 60)
        
        # 1. 잠재적 충돌 식별
        print("🔍 Step 1: Identifying Potential Conflicts")
        conflicts = self.identify_potential_conflicts()
        print(f"   Found {len(conflicts)} potential conflict pairs")
        
        # 2. 테스트 시나리오 생성
        print("🔍 Step 2: Generating Test Scenarios")
        scenarios = self.create_conflict_test_scenarios(conflicts)
        print(f"   Generated {len(scenarios)} test scenarios")
        
        # 3. 시나리오별 테스트 실행
        print("🔍 Step 3: Running Test Scenarios")
        results = {
            'total_scenarios': len(scenarios),
            'passed': 0,
            'failed': 0,
            'performance_tests': [],
            'conflict_resolutions': [],
            'pattern_statistics': defaultdict(int),
            'detailed_results': []
        }
        
        start_time = time.perf_counter()
        
        for i, scenario in enumerate(scenarios):
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(scenarios)} scenarios")
            
            # 시나리오 실행
            test_result = self._run_single_scenario(scenario)
            results['detailed_results'].append(test_result)
            
            if test_result['passed']:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            # 통계 수집
            for pattern in test_result.get('matched_patterns', []):
                results['pattern_statistics'][pattern] += 1
        
        end_time = time.perf_counter()
        results['total_execution_time'] = end_time - start_time
        
        # 4. 성능 테스트
        print("🔍 Step 4: Performance Analysis")
        perf_results = self._run_performance_tests()
        results['performance_tests'] = perf_results
        
        # 5. 결과 분석
        print("🔍 Step 5: Results Analysis")
        analysis = self._analyze_results(results)
        results['analysis'] = analysis
        
        return results
    
    def _run_single_scenario(self, scenario: Dict) -> Dict:
        """단일 시나리오 실행"""
        try:
            matches = self.patterns.find_matches(scenario['test_text'])
            matched_patterns = [m['pattern_name'] for m in matches]
            
            result = {
                'scenario_id': scenario['scenario_id'],
                'conflict_type': scenario['conflict_type'],
                'test_text': scenario['test_text'][:100] + '...' if len(scenario['test_text']) > 100 else scenario['test_text'],
                'matched_patterns': matched_patterns,
                'match_count': len(matches),
                'passed': True,
                'details': {}
            }
            
            # Overlap 시나리오 검증
            if 'overlap' in scenario['conflict_type']:
                expected_winner = scenario.get('expected_winner')
                if len(matched_patterns) == 1 and matched_patterns[0] == expected_winner:
                    result['details']['overlap_resolution'] = 'correct'
                elif len(matched_patterns) > 1:
                    result['details']['overlap_resolution'] = 'multiple_matches'
                    result['passed'] = False
                else:
                    result['details']['overlap_resolution'] = 'unexpected_winner'
                    result['passed'] = False
            
            return result
            
        except Exception as e:
            return {
                'scenario_id': scenario['scenario_id'],
                'passed': False,
                'error': str(e),
                'test_text': scenario['test_text'][:100] + '...'
            }
    
    def _run_performance_tests(self) -> List[Dict]:
        """성능 테스트 실행"""
        perf_tests = []
        
        # 1. 대용량 텍스트 처리 테스트
        large_text = " ".join([
            self.generate_realistic_test_data()[pattern] 
            for pattern in self.all_pattern_names[:20]
        ] * 10)  # 200개 패턴이 포함된 텍스트
        
        start_time = time.perf_counter()
        matches = self.patterns.find_matches(large_text)
        end_time = time.perf_counter()
        
        perf_tests.append({
            'test_name': 'large_text_processing',
            'text_length': len(large_text),
            'match_count': len(matches),
            'processing_time': end_time - start_time,
            'chars_per_second': len(large_text) / (end_time - start_time),
            'passed': (end_time - start_time) < 2.0
        })
        
        # 2. 패턴별 개별 성능 테스트
        test_data = self.generate_realistic_test_data()
        pattern_perfs = []
        
        for pattern_name in self.all_pattern_names[:10]:  # 상위 10개 패턴만
            if pattern_name in test_data:
                text = test_data[pattern_name] * 100  # 100회 반복
                
                start_time = time.perf_counter()
                matches = self.patterns.find_matches(text)
                end_time = time.perf_counter()
                
                pattern_perfs.append({
                    'pattern': pattern_name,
                    'processing_time': end_time - start_time,
                    'matches': len(matches)
                })
        
        perf_tests.append({
            'test_name': 'individual_pattern_performance',
            'results': pattern_perfs
        })
        
        return perf_tests
    
    def _analyze_results(self, results: Dict) -> Dict:
        """결과 분석"""
        analysis = {
            'success_rate': results['passed'] / results['total_scenarios'] if results['total_scenarios'] > 0 else 0,
            'most_matched_patterns': dict(sorted(results['pattern_statistics'].items(), key=lambda x: x[1], reverse=True)[:10]),
            'performance_summary': {
                'avg_processing_time': results['total_execution_time'] / results['total_scenarios'],
                'meets_performance_requirements': results['total_execution_time'] < (2.0 * results['total_scenarios'] / 100)
            },
            'recommendations': []
        }
        
        # 권장사항 생성
        if analysis['success_rate'] < 0.95:
            analysis['recommendations'].append("Some conflict scenarios failed - review overlap detection logic")
        
        if not analysis['performance_summary']['meets_performance_requirements']:
            analysis['recommendations'].append("Performance optimization needed for large-scale scenarios")
        
        # 패턴 사용률 분석
        unused_patterns = set(self.all_pattern_names) - set(results['pattern_statistics'].keys())
        if unused_patterns:
            analysis['unused_patterns'] = list(unused_patterns)
            analysis['recommendations'].append(f"Consider reviewing {len(unused_patterns)} unused patterns")
        
        return analysis
    
    def print_comprehensive_report(self, results: Dict):
        """상세 보고서 출력"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("="*60)
        
        # 전체 요약
        print(f"📈 Overall Results:")
        print(f"   Total Scenarios: {results['total_scenarios']}")
        print(f"   Passed: {results['passed']} ({results['passed']/results['total_scenarios']*100:.1f}%)")
        print(f"   Failed: {results['failed']} ({results['failed']/results['total_scenarios']*100:.1f}%)")
        print(f"   Execution Time: {results['total_execution_time']:.3f}s")
        
        # 성능 분석
        print(f"\n⚡ Performance Analysis:")
        for perf_test in results['performance_tests']:
            if perf_test['test_name'] == 'large_text_processing':
                print(f"   Large Text Processing:")
                print(f"     - Text Length: {perf_test['text_length']:,} chars")
                print(f"     - Processing Time: {perf_test['processing_time']:.3f}s")
                print(f"     - Performance: {perf_test['chars_per_second']:,.0f} chars/second")
                print(f"     - Status: {'✅ PASSED' if perf_test['passed'] else '❌ FAILED'}")
        
        # 패턴 통계
        print(f"\n📊 Pattern Usage Statistics (Top 10):")
        for pattern, count in results['analysis']['most_matched_patterns'].items():
            print(f"   {pattern:20s}: {count:3d} matches")
        
        # 권장사항
        if results['analysis']['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(results['analysis']['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # 최종 평가
        success_rate = results['analysis']['success_rate']
        if success_rate >= 0.95:
            print(f"\n🎉 EXCELLENT: {success_rate:.1%} success rate - System is production ready!")
        elif success_rate >= 0.90:
            print(f"\n✅ GOOD: {success_rate:.1%} success rate - Minor improvements needed")
        else:
            print(f"\n⚠️  NEEDS WORK: {success_rate:.1%} success rate - Significant improvements required")


def main():
    """메인 실행 함수"""
    framework = ComprehensiveTestFramework()
    
    print("Starting comprehensive test framework...")
    print(f"Total patterns to test: {len(framework.all_pattern_names)}")
    
    # 테스트 실행
    results = framework.run_comprehensive_tests()
    
    # 결과 보고서
    framework.print_comprehensive_report(results)
    
    # JSON 파일로 상세 결과 저장
    with open('comprehensive_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: comprehensive_test_results.json")
    print("🎉 Comprehensive testing complete!")


if __name__ == "__main__":
    main()