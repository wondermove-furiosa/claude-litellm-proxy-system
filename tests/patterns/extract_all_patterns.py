#!/usr/bin/env python3
"""
소스코드에서 모든 AWS 리소스 패턴을 추출하고 상세 분석

현재 cloud_patterns.py에 정의된 모든 패턴을 분석하여:
1. 패턴별 우선순위
2. 패턴별 정규식
3. 패턴별 유형
4. 실제 동작 여부
를 종합 검증
"""

import sys
import os
sys.path.append('.')

from src.claude_litellm_proxy.patterns.cloud_patterns import CloudPatterns
from typing import Dict, List, Any
import json
import re

def extract_and_analyze_all_patterns():
    """모든 패턴 추출 및 분석"""
    print("🔍 소스코드 기반 AWS 리소스 패턴 상세 분석")
    print("=" * 80)
    
    # CloudPatterns 인스턴스 생성
    cloud_patterns = CloudPatterns()
    
    # 내부 패턴 정의 접근 (private attribute)
    all_patterns = cloud_patterns._patterns
    
    print(f"📊 총 정의된 패턴 수: {len(all_patterns)} 개")
    
    # 패턴별 상세 정보 수집
    pattern_analysis = {}
    
    for pattern_name, pattern_def in all_patterns.items():
        pattern_info = {
            "pattern_name": pattern_name,
            "priority": pattern_def.priority,
            "type": pattern_def.type,
            "regex_pattern": pattern_def.pattern,
            "description": pattern_def.description,
            "replacement_template": pattern_def.replacement,
            "has_validator": pattern_def.validator is not None,
            "validator_name": pattern_def.validator.__name__ if pattern_def.validator else None
        }
        
        pattern_analysis[pattern_name] = pattern_info
    
    # 우선순위별로 정렬
    sorted_patterns = sorted(
        pattern_analysis.items(), 
        key=lambda x: x[1]["priority"]
    )
    
    # 우선순위별 분류 및 출력
    priority_groups = {}
    for pattern_name, info in sorted_patterns:
        priority = info["priority"]
        if priority not in priority_groups:
            priority_groups[priority] = []
        priority_groups[priority].append((pattern_name, info))
    
    print(f"\n📋 우선순위별 패턴 분류 (낮은 숫자 = 높은 우선순위)")
    print("-" * 80)
    
    total_verified_patterns = 0
    
    for priority in sorted(priority_groups.keys()):
        patterns_in_group = priority_groups[priority]
        print(f"\n🎯 Priority {priority}: {len(patterns_in_group)}개 패턴")
        
        for pattern_name, info in patterns_in_group:
            print(f"  ✓ {pattern_name:20} -> {info['type']:15} ({info['description']})")
            if info['has_validator']:
                print(f"    🔍 Validator: {info['validator_name']}")
            total_verified_patterns += 1
    
    print(f"\n📈 총 검증 대상 패턴: {total_verified_patterns} 개")
    
    return pattern_analysis, priority_groups

def test_patterns_with_real_samples():
    """실제 샘플 데이터로 패턴 테스트"""
    print("\n🧪 실제 샘플 데이터로 패턴 동작 검증")
    print("=" * 80)
    
    cloud_patterns = CloudPatterns()
    
    # 실제 AWS 리소스 샘플 데이터 (더 포괄적)
    test_samples = {
        # 컴퓨팅 서비스
        "fargate_task": [
            "arn:aws:ecs:us-east-1:123456789012:task/my-fargate-cluster/1234abcd-12ab-34cd-56ef-1234567890ab",
            "arn:aws:ecs:eu-west-1:987654321098:task/prod-cluster/abcdef12-34cd-56ef-78ab-90cd12345678"
        ],
        "lambda_arn": [
            "arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment",
            "arn:aws:lambda:eu-west-1:987654321098:function:user-authentication"
        ],
        "ecs_task": [
            "arn:aws:ecs:us-east-1:123456789012:task-definition/web-app:1",
            "arn:aws:ecs:eu-west-1:987654321098:task-definition/api-service:23"
        ],
        "ec2_instance": [
            "i-0123456789abcdef0",
            "i-abcdef1234567890a"
        ],
        "ami_id": [
            "ami-0123456789abcdef0",
            "ami-abcdef1234567890a"
        ],
        
        # 네트워킹 서비스
        "vpc": [
            "vpc-12345678",
            "vpc-abcdef12"
        ],
        "subnet": [
            "subnet-12345678901234567",
            "subnet-98765432109876543"
        ],
        "security_group": [
            "sg-0123456789abcdef0",
            "sg-abcdef1234567890a"
        ],
        "internet_gateway": [
            "igw-0123456789abcdef0",
            "igw-abcdef1234567890a"
        ],
        
        # 스토리지 서비스
        "s3_bucket": [
            "my-production-bucket",
            "company-data-lake-2024"
        ],
        "ebs_volume": [
            "vol-0123456789abcdef0",
            "vol-abcdef1234567890a"
        ],
        "snapshot": [
            "snap-0123456789abcdef0",
            "snap-abcdef1234567890a"
        ],
        "efs_filesystem": [
            "fs-0123456789abcdef0",
            "fs-abcdef1234567890a"
        ],
        
        # 보안 및 자격증명
        "access_key": [
            "AKIA1234567890ABCDEF",
            "AKIAXYZ789ABC123DEFG"
        ],
        "secret_key": [
            "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "1234567890abcdef1234567890abcdef12345678"
        ],
        "session_token": [
            "AQoEXAMPLEH4aoAH0gNCAPyJxz4BlCFFxWNE1OPTgk5TthT+FvwqnKwRcOIfrRh3c/LTo6UDdyJwOOvEVPvLXCrrrUtdnniCEXAMPLE",
            "FwoGZXIvYXdzEBQaDGg3S1NnVGZjZ1ZGOyKKASEMAMPLEsessiontokenexample1234567890"
        ],
        "kms_key": [
            "12345678-1234-1234-1234-123456789012",
            "abcdef12-3456-7890-abcd-ef1234567890"
        ],
        "account_id": [
            "123456789012",
            "987654321098"
        ],
        
        # 네트워크 리소스
        "public_ip": [
            "8.8.8.8",
            "1.1.1.1",
            "203.0.113.12",  # RFC 3849 Documentation IP
            "198.51.100.45"  # RFC 3849 Documentation IP
        ],
        "ipv6": [
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "2001:db8::1"
        ],
        
        # 기타 AWS 서비스
        "apprunner_service": [
            "arn:aws:apprunner:us-east-1:123456789012:service/my-app-service/8fe1e10304374e7c80684681ea1967",
            "arn:aws:apprunner:eu-west-1:987654321098:service/prod-service/1234567890abcdef1234567890abcd"
        ],
        "insights_query": [
            "12345678-1234-1234-1234-123456789012",
            "abcd1234-ef56-7890-abcd-ef1234567890",
            "87654321-4321-8765-4321-876543218765"
        ]
    }
    
    # 각 패턴별 테스트 실행
    working_patterns = []
    failed_patterns = []
    partial_patterns = []
    
    for pattern_name, samples in test_samples.items():
        print(f"\n🔍 테스트: {pattern_name}")
        
        successful_samples = 0
        total_samples = len(samples)
        
        for sample in samples:
            try:
                matches = cloud_patterns.find_matches(f"Resource: {sample}")
                
                # 해당 패턴이 검출되었는지 확인
                pattern_detected = False
                detected_types = []
                
                for match in matches:
                    if pattern_name in match.get('pattern_name', '') or \
                       any(expected_type in match.get('type', '') for expected_type in [pattern_name.split('_')[0], pattern_name]):
                        pattern_detected = True
                        detected_types.append(match.get('type', 'unknown'))
                
                if pattern_detected:
                    successful_samples += 1
                    print(f"  ✅ {sample[:50]:50} -> {detected_types}")
                else:
                    print(f"  ❌ {sample[:50]:50} -> No match")
                    
            except Exception as e:
                print(f"  💥 {sample[:50]:50} -> Error: {e}")
        
        # 패턴 분류
        success_rate = (successful_samples / total_samples) * 100
        
        if success_rate == 100:
            working_patterns.append({
                "pattern": pattern_name,
                "success_rate": success_rate,
                "samples": samples,
                "status": "fully_working"
            })
            print(f"  🎉 {pattern_name}: {success_rate:.1f}% ({successful_samples}/{total_samples}) - 완전 작동")
        elif success_rate >= 50:
            partial_patterns.append({
                "pattern": pattern_name,
                "success_rate": success_rate,
                "samples": samples,
                "status": "partially_working"
            })
            print(f"  ⚠️  {pattern_name}: {success_rate:.1f}% ({successful_samples}/{total_samples}) - 부분 작동")
        else:
            failed_patterns.append({
                "pattern": pattern_name,
                "success_rate": success_rate,
                "samples": samples,
                "status": "failed"
            })
            print(f"  ❌ {pattern_name}: {success_rate:.1f}% ({successful_samples}/{total_samples}) - 작동 실패")
    
    # 결과 요약
    print(f"\n📊 패턴 검증 결과 요약")
    print("-" * 80)
    print(f"✅ 완전 작동: {len(working_patterns)}개")
    print(f"⚠️  부분 작동: {len(partial_patterns)}개") 
    print(f"❌ 작동 실패: {len(failed_patterns)}개")
    print(f"📈 전체 패턴: {len(test_samples)}개")
    
    overall_success_rate = (len(working_patterns) / len(test_samples)) * 100
    print(f"🎯 전체 성공률: {overall_success_rate:.1f}%")
    
    return {
        "working_patterns": working_patterns,
        "partial_patterns": partial_patterns,
        "failed_patterns": failed_patterns,
        "overall_success_rate": overall_success_rate,
        "total_tested": len(test_samples)
    }

def analyze_priority_system():
    """우선순위 시스템 분석"""
    print("\n🎯 우선순위 시스템 기술적 분석")
    print("=" * 80)
    
    cloud_patterns = CloudPatterns()
    
    # 충돌 가능한 샘플 텍스트로 우선순위 검증
    conflict_test_cases = [
        {
            "text": "arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment",
            "description": "Lambda ARN vs Generic ARN 충돌 테스트",
            "expected_priority": "lambda_arn (높은 우선순위) > arn (낮은 우선순위)"
        },
        {
            "text": "Resource arn:aws:s3:::my-bucket with account 123456789012",
            "description": "S3 ARN vs Account ID 충돌 테스트",
            "expected_priority": "더 긴 매치가 우선되어야 함"
        },
        {
            "text": "12345678-1234-1234-1234-123456789012",
            "description": "KMS Key vs Insights Query UUID 충돌 테스트",
            "expected_priority": "insights_query (P75) > kms_key (P370)"
        }
    ]
    
    for i, test_case in enumerate(conflict_test_cases, 1):
        print(f"\n🔍 충돌 테스트 {i}: {test_case['description']}")
        print(f"입력: {test_case['text']}")
        
        # 충돌 해결 없이 모든 매치 찾기
        matches = cloud_patterns.find_matches(test_case['text'], resolve_conflicts=False)
        print(f"발견된 매치: {len(matches)}개")
        
        for match in matches:
            print(f"  - {match['match'][:30]:30} -> {match.get('type', 'unknown'):12} (P{match.get('priority', 'N/A'):3})")
        
        # 충돌 해결 후 결과
        resolved_matches = cloud_patterns.find_matches(test_case['text'], resolve_conflicts=True)
        print(f"충돌 해결 후: {len(resolved_matches)}개")
        
        for match in resolved_matches:
            print(f"  ✅ {match['match'][:30]:30} -> {match.get('type', 'unknown'):12} (P{match.get('priority', 'N/A'):3}) - 선택됨")
    
    return True

def save_detailed_analysis(pattern_analysis, test_results):
    """상세 분석 결과 저장"""
    detailed_report = {
        "analysis_timestamp": "2025-01-23T00:00:00Z",
        "total_patterns_defined": len(pattern_analysis),
        "pattern_definitions": pattern_analysis,
        "test_results": test_results,
        "priority_analysis": {
            "priority_groups": {},
            "conflict_resolution": "길이 우선 + 우선순위 기반 그리디 알고리즘"
        }
    }
    
    # 우선순위별 그룹핑
    for pattern_name, info in pattern_analysis.items():
        priority = info["priority"]
        if priority not in detailed_report["priority_analysis"]["priority_groups"]:
            detailed_report["priority_analysis"]["priority_groups"][priority] = []
        detailed_report["priority_analysis"]["priority_groups"][priority].append(pattern_name)
    
    # 결과 저장
    with open("detailed_pattern_analysis.json", "w", encoding="utf-8") as f:
        json.dump(detailed_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 상세 분석 보고서 저장: detailed_pattern_analysis.json")
    
    return detailed_report

if __name__ == "__main__":
    try:
        # 1. 모든 패턴 추출 및 분석
        pattern_analysis, priority_groups = extract_and_analyze_all_patterns()
        
        # 2. 실제 샘플로 패턴 테스트
        test_results = test_patterns_with_real_samples()
        
        # 3. 우선순위 시스템 분석
        analyze_priority_system()
        
        # 4. 상세 분석 결과 저장
        detailed_report = save_detailed_analysis(pattern_analysis, test_results)
        
        print("\n🎉 소스코드 기반 AWS 리소스 패턴 상세 분석 완료!")
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()