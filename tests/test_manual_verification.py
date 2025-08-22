#!/usr/bin/env python3
"""
수동 검증 스크립트 - 실제 마스킹 기능이 정상 작동하는지 확인
사용자 지적 사항: 테스트가 성공했지만 실제 기능이 구현되었는지 의문
"""

from src.claude_litellm_proxy.patterns.masking_engine import MaskingEngine

def main():
    print("🧪 실제 마스킹 기능 수동 검증")
    print("=" * 50)
    
    engine = MaskingEngine()
    
    # 테스트 1: EC2 인스턴스 ID
    print("\n1. EC2 인스턴스 ID 마스킹:")
    ec2_text = "EC2 instance i-1234567890abcdef0 is running"
    masked, mapping = engine.mask_text(ec2_text)
    print(f"원본: {ec2_text}")
    print(f"마스킹: {masked}")
    print(f"매핑: {mapping}")
    
    # 테스트 2: IAM Access Key
    print("\n2. IAM Access Key 마스킹:")
    iam_text = "Use access key AKIA1234567890ABCDEF for authentication"
    masked, mapping = engine.mask_text(iam_text)
    print(f"원본: {iam_text}")
    print(f"마스킹: {masked}")
    print(f"매핑: {mapping}")
    
    # 테스트 3: S3 버킷
    print("\n3. S3 버킷 마스킹:")
    s3_text = "Store files in my-company-logs-bucket"
    masked, mapping = engine.mask_text(s3_text)
    print(f"원본: {s3_text}")
    print(f"마스킹: {masked}")
    print(f"매핑: {mapping}")
    
    # 테스트 4: 복합 텍스트 (핵심 검증)
    print("\n4. 복합 텍스트 마스킹 (핵심 검증):")
    complex_text = """
    EC2 instance i-1234567890abcdef0 is running in VPC vpc-12345678
    with security group sg-87654321 and uses IAM role with key AKIA1234567890ABCDEF.
    Data is stored in S3 bucket my-prod-data-bucket.
    """
    
    print(f"원본:\n{complex_text}")
    
    masked, mapping = engine.mask_text(complex_text)
    
    print(f"\n마스킹된 텍스트:\n{masked}")
    print(f"\n매핑 정보:")
    for masked_val, original_val in mapping.items():
        print(f"  {masked_val} → {original_val}")
    
    # 검증 결과 출력
    print("\n" + "=" * 50)
    print("🔍 검증 결과:")
    
    # 1. 원본 민감정보가 마스킹되었는지 확인
    sensitive_data = [
        "i-1234567890abcdef0",
        "vpc-12345678", 
        "sg-87654321",
        "AKIA1234567890ABCDEF",
        "my-prod-data-bucket"
    ]
    
    all_masked = True
    for sensitive in sensitive_data:
        if sensitive in masked:
            print(f"❌ 민감정보 노출: {sensitive}")
            all_masked = False
        else:
            print(f"✅ 마스킹 완료: {sensitive}")
    
    # 2. 매핑 개수 확인
    print(f"\n매핑 개수: {len(mapping)} (예상: 5)")
    if len(mapping) == 5:
        print("✅ 매핑 개수 정확")
    else:
        print("❌ 매핑 개수 불일치")
    
    # 3. 마스킹 형식 확인
    print(f"\n마스킹 형식 검증:")
    expected_prefixes = ["ec2-", "vpc-", "sg-", "iam-", "bucket-"]
    found_prefixes = []
    
    for masked_val in mapping.keys():
        for prefix in expected_prefixes:
            if masked_val.startswith(prefix):
                found_prefixes.append(prefix)
                print(f"✅ {prefix} 형식 확인: {masked_val}")
                break
    
    missing_prefixes = set(expected_prefixes) - set(found_prefixes)
    if missing_prefixes:
        print(f"❌ 누락된 형식: {missing_prefixes}")
    
    # 최종 결론
    print("\n" + "=" * 50)
    if all_masked and len(mapping) == 5 and not missing_prefixes:
        print("🎉 모든 검증 통과: 마스킹 기능이 정상 작동합니다!")
        return True
    else:
        print("❌ 검증 실패: 마스킹 기능에 문제가 있습니다!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)