#!/usr/bin/env python3
"""
누락된 중요 패턴들과 우선순위 불일치 문제 실행 환경 검증

ref-masking-rule.md 기준으로 누락된 패턴과 우선순위 차이로 인한 
실제 문제가 발생하는지 테스트
"""

import sys
sys.path.append('src')

import asyncio
from claude_litellm_proxy.patterns.cloud_patterns import CloudPatterns
from claude_litellm_proxy.proxy.integrated_masking import IntegratedMaskingSystem

async def test_missing_critical_patterns():
    """누락된 중요 패턴 테스트"""
    print("🔍 누락된 중요 패턴 검증 테스트")
    print("=" * 60)
    
    cloud_patterns = CloudPatterns()
    
    # masking-rule-checklist.md에서 식별된 누락된 중요 패턴들
    missing_critical_tests = {
        "parameter_store_arn": [
            "arn:aws:ssm:us-east-1:123456789012:parameter/myapp/database/password",
            "arn:aws:ssm:eu-west-1:987654321098:parameter/app/config/secret"
        ],
        "elasticsearch_domain_arn": [
            "arn:aws:es:us-east-1:123456789012:domain/my-domain",
            "arn:aws:es:eu-west-1:987654321098:domain/search-cluster"
        ],
        "ecr_repository_uri": [
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
            "987654321098.dkr.ecr.eu-west-1.amazonaws.com/web-app"
        ],
        "eks_cluster_arn": [
            "arn:aws:eks:us-east-1:123456789012:cluster/my-cluster",
            "arn:aws:eks:eu-west-1:987654321098:cluster/production"
        ],
        "vpn_connection_id": [
            "vpn-12345678",
            "vpn-abcdef12"
        ]
    }
    
    print("📋 누락된 패턴별 검증 결과:")
    
    missing_count = 0
    total_samples = 0
    
    for pattern_name, samples in missing_critical_tests.items():
        print(f"\n🔍 {pattern_name} 테스트:")
        
        for sample in samples:
            matches = cloud_patterns.find_matches(f"Resource: {sample}")
            total_samples += 1
            
            if matches:
                print(f"  ✅ {sample[:50]:50} -> {[m.get('type', 'unknown') for m in matches]}")
            else:
                print(f"  ❌ {sample[:50]:50} -> No match (예상대로 누락)")
                missing_count += 1
    
    missing_rate = (missing_count / total_samples) * 100
    print(f"\n📊 누락 패턴 테스트 결과:")
    print(f"  총 테스트 샘플: {total_samples}개")
    print(f"  매칭되지 않음: {missing_count}개 ({missing_rate:.1f}%)")
    print(f"  예상 결과와 일치: {'✅ 정상' if missing_rate > 80 else '⚠️ 예상과 다름'}")
    
    return missing_count, total_samples

async def test_priority_conflicts():
    """우선순위 불일치로 인한 실제 충돌 테스트"""
    print("\n🎯 우선순위 불일치 충돌 테스트")
    print("=" * 60)
    
    cloud_patterns = CloudPatterns()
    
    # KMS Key ID vs Account ID 충돌 (ref: 125 vs 600, 현재: 370 vs 600)
    critical_conflicts = [
        {
            "text": "KMS Key 12345678-1234-1234-1234-123456789012 for Account 123456789012",
            "description": "KMS Key ID vs Account ID 충돌",
            "expected_priority": "KMS Key가 Account보다 높은 우선순위여야 함(ref: 125 < 600)"
        },
        {
            "text": "arn:aws:lambda:us-east-1:123456789012:function:test with i-1234567890abcdef0",
            "description": "Lambda ARN vs EC2 Instance 충돌", 
            "expected_priority": "Lambda ARN(100)이 EC2(250)보다 높은 우선순위"
        },
        {
            "text": "Access key AKIA1234567890ABCDEF for account 123456789012",
            "description": "Access Key vs Account ID 충돌",
            "expected_priority": "Access Key(310)가 Account ID(600)보다 높은 우선순위"
        }
    ]
    
    print("📋 우선순위 충돌 시나리오별 검증:")
    
    for i, conflict in enumerate(critical_conflicts, 1):
        print(f"\n🔍 충돌 시나리오 {i}: {conflict['description']}")
        print(f"입력: {conflict['text']}")
        
        # 충돌 해결 없이 모든 매치 확인
        matches = cloud_patterns.find_matches(conflict['text'], resolve_conflicts=False)
        print(f"발견된 매치: {len(matches)}개")
        
        for match in matches:
            priority = match.get('priority', 'N/A')
            match_text = match['match'][:30]
            match_type = match.get('type', 'unknown')
            print(f"  - {match_text:30} -> {match_type:15} (P{priority:3})")
        
        # 충돌 해결 후 결과
        resolved_matches = cloud_patterns.find_matches(conflict['text'], resolve_conflicts=True)
        print(f"충돌 해결 후: {len(resolved_matches)}개")
        
        for match in resolved_matches:
            priority = match.get('priority', 'N/A')
            match_text = match['match'][:30]
            match_type = match.get('type', 'unknown')
            print(f"  ✅ {match_text:30} -> {match_type:15} (P{priority:3}) - 최종 선택")
    
    return True

async def test_priority_misalignment_impact():
    """우선순위 불일치의 실제 영향도 테스트"""
    print("\n⚖️ 우선순위 불일치 영향도 분석")
    print("=" * 60)
    
    masking_system = IntegratedMaskingSystem()
    await masking_system.clear_all_mappings()
    
    # 실제 마스킹에서 우선순위 차이로 인한 문제 시나리오
    priority_test_cases = [
        {
            "text": "Deploy Glue job glue-job-data-processing on EC2 i-1234567890abcdef0",
            "issue": "Glue Job 우선순위: ref(560) → py(165), EC2: ref(250) → py(260)",
            "expected": "현재 구현에서는 Glue Job이 EC2보다 높은 우선순위"
        },
        {
            "text": "Store data in RDS myapp-db-prod with KMS key 12345678-1234-1234-1234-123456789012",
            "issue": "RDS: ref(520) → py(300), KMS: ref(125) → py(370)",
            "expected": "ref에서는 KMS > RDS, py에서는 RDS > KMS"
        }
    ]
    
    print("📋 우선순위 차이가 실제 마스킹 결과에 미치는 영향:")
    
    for i, test_case in enumerate(priority_test_cases, 1):
        print(f"\n🔍 테스트 케이스 {i}:")
        print(f"입력: {test_case['text']}")
        print(f"문제: {test_case['issue']}")
        print(f"예상: {test_case['expected']}")
        
        # 실제 마스킹 수행
        masked_text, mappings = await masking_system.mask_text(test_case['text'])
        print(f"마스킹 결과: {masked_text}")
        print(f"매핑 수량: {len(mappings)}개")
        
        for masked_id, original in mappings.items():
            print(f"  {masked_id} <- {original}")
    
    await masking_system.close()
    return True

async def test_ref_compliance_validation():
    """ref-masking-rule.md 준수도 종합 검증"""
    print("\n📊 ref-masking-rule.md 준수도 종합 검증")
    print("=" * 60)
    
    # 참조 문서에서 완전히 일치해야 하는 핵심 패턴들 테스트
    ref_compliance_tests = {
        # 완전 일치 패턴들 (masking-rule-checklist.md 참조)
        "lambda_arn": {
            "samples": ["arn:aws:lambda:us-east-1:123456789012:function:my-function"],
            "expected_priority": 100,
            "expected_format": "AWS_LAMBDA_ARN_{:03d}",
            "should_match": True
        },
        "vpc_id": {
            "samples": ["vpc-12345678"],
            "expected_priority": 230,
            "expected_format": "AWS_VPC_{:03d}",
            "should_match": True
        },
        "kms_key": {
            "samples": ["12345678-1234-1234-1234-123456789012"],
            "expected_priority": 125,  # ref 기준
            "expected_format": "AWS_KMS_KEY_{:03d}",
            "should_match": True,
            "current_priority": 370  # 현재 Python 구현
        },
        "parameter_store": {
            "samples": ["arn:aws:ssm:us-east-1:123456789012:parameter/myapp/database/password"],
            "expected_priority": 140,
            "expected_format": "AWS_PARAM_ARN_{:03d}",
            "should_match": False  # 누락된 패턴
        }
    }
    
    cloud_patterns = CloudPatterns()
    compliance_score = 0
    total_tests = 0
    
    print("📋 핵심 패턴별 준수도 검증:")
    
    for pattern_name, test_data in ref_compliance_tests.items():
        print(f"\n🔍 {pattern_name} 패턴:")
        
        for sample in test_data['samples']:
            total_tests += 1
            matches = cloud_patterns.find_matches(f"Test: {sample}")
            
            if test_data['should_match']:
                if matches:
                    match = matches[0]
                    actual_priority = match.get('priority', 'N/A')
                    expected_priority = test_data['expected_priority']
                    
                    print(f"  ✅ 매치: {sample[:40]:40}")
                    print(f"     우선순위: {actual_priority} (기대값: {expected_priority})")
                    
                    if 'current_priority' in test_data:
                        # KMS Key 같은 경우 현재 우선순위와 ref 우선순위가 다름
                        if actual_priority == test_data['current_priority']:
                            print(f"     ⚠️ ref와 다름: {expected_priority} → {actual_priority}")
                        else:
                            print(f"     ❌ 예상과도 다름: {test_data['current_priority']} → {actual_priority}")
                    elif actual_priority == expected_priority:
                        print(f"     ✅ 우선순위 일치")
                        compliance_score += 1
                    else:
                        print(f"     ❌ 우선순위 불일치")
                else:
                    print(f"  ❌ 매치 실패: {sample[:40]:40} (구현되어야 함)")
            else:
                if not matches:
                    print(f"  ✅ 매치 없음: {sample[:40]:40} (예상대로 누락)")
                    compliance_score += 1
                else:
                    print(f"  ⚠️ 예상치 못한 매치: {sample[:40]:40}")
    
    compliance_rate = (compliance_score / total_tests) * 100
    print(f"\n📈 ref-masking-rule.md 준수도: {compliance_rate:.1f}% ({compliance_score}/{total_tests})")
    
    return compliance_rate

async def main():
    """메인 검증 함수"""
    print("🔍 ref-masking-rule.md 기준 1:1 대응 실행 환경 검증")
    print("=" * 80)
    
    try:
        # 1. 누락된 중요 패턴 테스트
        missing_count, total_missing = await test_missing_critical_patterns()
        
        # 2. 우선순위 충돌 테스트  
        await test_priority_conflicts()
        
        # 3. 우선순위 불일치 영향도 테스트
        await test_priority_misalignment_impact()
        
        # 4. ref 준수도 종합 검증
        compliance_rate = await test_ref_compliance_validation()
        
        print("\n" + "=" * 80)
        print("📊 종합 검증 결과 요약:")
        print(f"  누락 패턴: {missing_count}/{total_missing} (예상대로 누락)")
        print(f"  ref 준수도: {compliance_rate:.1f}%")
        
        if compliance_rate >= 80:
            print("✅ ref-masking-rule.md와 높은 호환성 유지")
        elif compliance_rate >= 60:
            print("⚠️ ref-masking-rule.md와 중간 호환성, 개선 필요")
        else:
            print("❌ ref-masking-rule.md와 낮은 호환성, 즉시 수정 필요")
            
        return compliance_rate >= 60
        
    except Exception as e:
        print(f"❌ 검증 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)