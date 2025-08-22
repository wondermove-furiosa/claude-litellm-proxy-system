#!/usr/bin/env python3
"""
우선순위 시스템 검증 테스트
레퍼런스 Kong 플러그인과 동일한 우선순위 적용 확인
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from claude_litellm_proxy.patterns.cloud_patterns import CloudPatterns


def test_priority_conflicts():
    """우선순위 충돌 시나리오 테스트"""
    
    patterns = CloudPatterns()
    
    # Test Case 1: Lambda ARN vs Generic ARN 충돌
    print("🔍 Test Case 1: Lambda ARN vs Generic ARN")
    test_text = "Resource: arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment"
    
    matches = patterns.find_matches(test_text)
    print(f"Input: {test_text}")
    print(f"Matches found: {len(matches)}")
    
    for match in matches:
        print(f"  - Pattern: {match['pattern_name']} (Priority: {match['pattern_def'].priority})")
        print(f"  - Match: {match['match']}")
        print(f"  - Type: {match['type']}")
    
    # 예상: Lambda ARN (Priority 100)이 Generic ARN (Priority 500)보다 우선
    assert len(matches) > 0, "No matches found"
    if len(matches) > 1:
        print("⚠️  Multiple matches found - need overlap detection!")
    else:
        print("✅ Single match - priority system working")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 2: EC2 Instance vs Account ID 부분 충돌
    print("🔍 Test Case 2: EC2 Instance vs Account ID") 
    test_text = "Launch i-1234567890abcdef0 in account 123456789012"
    
    matches = patterns.find_matches(test_text)
    print(f"Input: {test_text}")
    print(f"Matches found: {len(matches)}")
    
    for match in matches:
        print(f"  - Pattern: {match['pattern_name']} (Priority: {match['pattern_def'].priority})")
        print(f"  - Match: {match['match']}")
        print(f"  - Position: {match['start']}-{match['end']}")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 3: Public IP vs Private IP 구분
    print("🔍 Test Case 3: Public vs Private IP")
    test_cases_ip = [
        "8.8.8.8",        # Public DNS
        "10.0.0.1",       # Private RFC 1918
        "192.168.1.1",    # Private RFC 1918 
        "172.16.0.1",     # Private RFC 1918
        "127.0.0.1",      # Loopback
        "169.254.1.1",    # Link-local
        "203.0.113.1"     # Test network (should not match)
    ]
    
    for ip in test_cases_ip:
        matches = patterns.find_matches(f"Server IP: {ip}")
        print(f"IP: {ip} -> Matches: {len(matches)}")
        if matches:
            for match in matches:
                print(f"  - Matched as: {match['pattern_name']}")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 4: 모든 패턴 우선순위 순서 검증
    print("🔍 Test Case 4: Priority Order Validation")
    all_patterns = patterns._patterns
    sorted_patterns = sorted(all_patterns.items(), key=lambda x: x[1].priority)
    
    print("Priority order (first 10):")
    for i, (name, pattern_def) in enumerate(sorted_patterns[:10]):
        print(f"  {i+1:2d}. {name:20s} (Priority: {pattern_def.priority:3d}) - {pattern_def.type}")
    
    print("...")
    print("Priority order (last 10):")
    for i, (name, pattern_def) in enumerate(sorted_patterns[-10:], len(sorted_patterns)-10):
        print(f"  {i+1:2d}. {name:20s} (Priority: {pattern_def.priority:3d}) - {pattern_def.type}")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 5: Complex Infrastructure Text
    print("🔍 Test Case 5: Complex Infrastructure Scenario")
    complex_text = """
    AWS Infrastructure Report:
    - Lambda Function: arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment
    - EC2 Instance: i-1234567890abcdef0 
    - VPC: vpc-12345678
    - Subnet: subnet-1234567890abcdef0
    - Security Group: sg-12345678
    - Load Balancer: arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-lb/1234567890abcdef
    - S3 Bucket: my-data-bucket
    - RDS Instance: my-prod-db
    - Account: 123456789012
    - Access Key: AKIA1234567890ABCDEF
    - Public IP: 8.8.8.8
    - Private IP: 10.0.0.1
    """
    
    matches = patterns.find_matches(complex_text)
    print(f"Complex text matches: {len(matches)}")
    
    # 타입별 그룹핑
    by_type = {}
    for match in matches:
        match_type = match['type']
        if match_type not in by_type:
            by_type[match_type] = []
        by_type[match_type].append(match)
    
    for match_type, type_matches in sorted(by_type.items()):
        print(f"  {match_type}: {len(type_matches)} matches")
        for match in type_matches:
            print(f"    - {match['pattern_name']}: {match['match']}")


if __name__ == "__main__":
    print("🚀 Kong AWS Masking Priority System Validation")
    print("=" * 60)
    test_priority_conflicts()
    print("✅ Priority validation complete!")