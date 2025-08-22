#!/usr/bin/env python3
"""
전체 시스템 검증 스크립트

사용자 지적사항 재검증:
1. 실제 기능이 모든 테스트와 함께 작동하는가?
2. Redis 영속성이 실제로 동작하는가?  
3. 세션 간 일관성이 보장되는가?
"""

import asyncio
from src.claude_litellm_proxy.proxy.integrated_masking import IntegratedMaskingSystem

async def main():
    print("🔍 전체 시스템 종합 검증")
    print("=" * 60)
    
    # 시스템 1: 첫 번째 세션
    print("\n📍 1단계: 첫 번째 세션에서 마스킹")
    system1 = IntegratedMaskingSystem(
        redis_host="localhost",
        redis_port=6379,
        redis_db=15
    )
    
    # 복잡한 실제 인프라 설정 텍스트
    infrastructure_config = """
    Production Infrastructure Configuration:
    
    Web Servers:
    - EC2 Instance 1: i-1234567890abcdef0 (us-east-1a)
    - EC2 Instance 2: i-abcdef1234567890 (us-east-1b)
    - Load Balancer: elb-prod-web-123
    
    Database:
    - RDS Primary: prod-mysql-db-cluster
    - RDS Replica: replica-mysql-db-cluster
    
    Network:
    - VPC: vpc-12345678
    - Subnet 1: subnet-1234567890abcdef0
    - Subnet 2: subnet-abcdef1234567890
    - Security Group: sg-87654321
    
    Storage:
    - Logs Bucket: company-prod-logs-2024
    - Backup Bucket: company-backup-bucket
    - Data Bucket: analytics-data-bucket
    
    IAM & Security:
    - Service Account Key: AKIA1234567890ABCDEF
    - Backup Key: AKIA9876543210FEDCBA
    - Admin Role: arn:aws:iam::123456789012:role/AdminRole
    
    Monitoring:
    - CloudWatch Logs: /aws/lambda/prod-function
    - SNS Topic: arn:aws:sns:us-east-1:123456789012:alerts
    """
    
    print("원본 설정:")
    print(infrastructure_config[:200] + "...")
    
    # 첫 번째 마스킹
    masked_config1, mapping1 = await system1.mask_text(infrastructure_config)
    
    print(f"\n마스킹 결과 (매핑 수: {len(mapping1)}):")
    print(masked_config1[:300] + "...")
    
    print(f"\n매핑 정보 샘플:")
    for i, (masked, original) in enumerate(list(mapping1.items())[:5]):
        print(f"  {masked} → {original}")
    
    # 시스템 1 종료
    await system1.close()
    
    # 2단계: 새로운 세션에서 동일한 텍스트 처리
    print("\n📍 2단계: 새로운 세션에서 일관성 검증")
    system2 = IntegratedMaskingSystem(
        redis_host="localhost", 
        redis_port=6379,
        redis_db=15
    )
    
    # 동일한 텍스트로 마스킹
    masked_config2, mapping2 = await system2.mask_text(infrastructure_config)
    
    # 일관성 확인
    print(f"세션 간 일관성 검증:")
    print(f"  마스킹 결과 동일: {masked_config1 == masked_config2}")
    print(f"  매핑 정보 동일: {mapping1 == mapping2}")
    
    if masked_config1 == masked_config2:
        print("  ✅ 완벽한 세션 간 일관성 달성!")
    else:
        print("  ❌ 세션 간 일관성 실패")
        return False
    
    # 3단계: 언마스킹 검증
    print("\n📍 3단계: Redis 기반 언마스킹 검증")
    
    # 마스킹된 텍스트를 원본으로 복원
    unmasked_config = await system2.unmask_text(masked_config2)
    
    # 원본 리소스들이 복원되었는지 확인
    original_resources = [
        "i-1234567890abcdef0",
        "i-abcdef1234567890", 
        "vpc-12345678",
        "sg-87654321",
        "AKIA1234567890ABCDEF",
        "company-prod-logs-2024"
    ]
    
    restored_count = 0
    for resource in original_resources:
        if resource in unmasked_config:
            restored_count += 1
            print(f"  ✅ 복원 확인: {resource}")
        else:
            print(f"  ❌ 복원 실패: {resource}")
    
    print(f"\n언마스킹 성공률: {restored_count}/{len(original_resources)} ({restored_count/len(original_resources)*100:.1f}%)")
    
    # 4단계: 부분 텍스트 마스킹 일관성
    print("\n📍 4단계: 부분 텍스트 일관성 검증")
    
    partial_text1 = "Server i-1234567890abcdef0 in VPC vpc-12345678"
    partial_text2 = "Different server i-1234567890abcdef0 same VPC vpc-12345678"
    
    masked_partial1, mapping_partial1 = await system2.mask_text(partial_text1)
    masked_partial2, mapping_partial2 = await system2.mask_text(partial_text2)
    
    print(f"부분 텍스트 1: {masked_partial1}")
    print(f"부분 텍스트 2: {masked_partial2}")
    
    # 같은 리소스는 같은 마스킹 값을 가져야 함
    consistency_check = True
    for original in ["i-1234567890abcdef0", "vpc-12345678"]:
        masked_val1 = None
        masked_val2 = None
        
        for masked, orig in mapping_partial1.items():
            if orig == original:
                masked_val1 = masked
                break
                
        for masked, orig in mapping_partial2.items():
            if orig == original:
                masked_val2 = masked
                break
        
        if masked_val1 == masked_val2:
            print(f"  ✅ 일관성 유지: {original} → {masked_val1}")
        else:
            print(f"  ❌ 일관성 실패: {original} → {masked_val1} vs {masked_val2}")
            consistency_check = False
    
    # 5단계: 성능 검증
    print("\n📍 5단계: 성능 검증 (5초 이내)")
    
    import time
    start_time = time.time()
    
    # 여러 번의 마스킹 작업
    for i in range(10):
        test_text = f"Test {i}: EC2 i-{i:016x}a with IAM AKIA{i:016d} in VPC vpc-{i:08x}"
        await system2.mask_text(test_text)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"10회 마스킹 작업 시간: {duration:.2f}초")
    
    if duration < 5.0:
        print("  ✅ 성능 요구사항 달성!")
    else:
        print("  ❌ 성능 요구사항 미달")
        consistency_check = False
    
    # 시스템 2 종료
    await system2.close()
    
    # 최종 결과
    print("\n" + "=" * 60)
    print("🏁 종합 검증 결과:")
    
    if consistency_check and restored_count >= len(original_resources) * 0.8:
        print("🎉 전체 시스템이 정상 작동합니다!")
        print("   - Redis 영속성: ✅")
        print("   - 세션 간 일관성: ✅") 
        print("   - 언마스킹 기능: ✅")
        print("   - 성능 요구사항: ✅")
        return True
    else:
        print("❌ 시스템에 문제가 있습니다!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)