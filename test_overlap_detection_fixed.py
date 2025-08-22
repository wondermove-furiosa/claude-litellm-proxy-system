#!/usr/bin/env python3
"""
Overlap Detection Engine 성능 검증
레퍼런스 대비 혁신적 충돌 해결 알고리즘 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from claude_litellm_proxy.patterns.cloud_patterns import CloudPatterns
import json


def test_overlap_detection():
    """Overlap Detection Engine 핵심 기능 테스트"""
    
    patterns = CloudPatterns()
    patterns.enable_debug(True)  # 상세 로그 활성화
    
    print("🚀 Overlap Detection Engine Performance Test")
    print("=" * 60)
    
    # Test Case 1: Lambda ARN vs Account ID 충돌
    print("🔍 Test Case 1: Lambda ARN vs Account ID Conflict")
    test_text = "Deploy arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment"
    
    print("🔄 Before Overlap Detection:")
    raw_matches = patterns.find_matches(test_text, resolve_conflicts=False)
    print(f"Raw matches: {len(raw_matches)}")
    for match in raw_matches:
        print(f"  - {match['pattern_name']}: {match['match']} (Priority: {match['pattern_def'].priority})")
    
    print("\n✅ After Overlap Detection:")
    resolved_matches = patterns.find_matches(test_text, resolve_conflicts=True)
    print(f"Resolved matches: {len(resolved_matches)}")
    for match in resolved_matches:
        print(f"  - {match['pattern_name']}: {match['match']} (Priority: {match['pattern_def'].priority})")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 2: 복잡한 인프라 시나리오
    print("🔍 Test Case 2: Complex Infrastructure with Analysis")
    complex_text = """
    Infrastructure Setup:
    - Lambda: arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment
    - ELB: arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-lb/1234567890abcdef
    - EC2: i-1234567890abcdef0 in vpc-12345678
    - RDS: my-prod-db-instance
    - S3: my-data-bucket-prod
    - Account: 123456789012
    - Access Key: AKIA1234567890ABCDEF
    - Public IP: 8.8.8.8
    - Private IP: 10.0.0.1
    """
    
    resolved, analysis = patterns.find_matches_with_analysis(complex_text)
    
    print(f"📊 Analysis Results:")
    print(f"  - Original matches: {analysis['efficiency']['original_matches']}")
    print(f"  - Resolved matches: {analysis['efficiency']['resolved_matches']}")
    print(f"  - Reduction rate: {analysis['efficiency']['reduction_rate']:.1%}")
    print(f"  - Conflicts resolved: {analysis['conflicts_resolved']}")
    print(f"  - Conflict groups: {analysis['conflict_groups']}")
    
    print(f"\n🎯 Final Matches by Type:")
    by_type = {}
    for match in resolved:
        match_type = match['type']
        if match_type not in by_type:
            by_type[match_type] = []
        by_type[match_type].append(match)
    
    for match_type in sorted(by_type.keys()):
        print(f"  {match_type}: {len(by_type[match_type])} matches")
        for match in by_type[match_type]:
            print(f"    - {match['pattern_name']}: {match['match']}")
    
    # 충돌 상세 분석
    if analysis['groups']:
        print(f"\n⚔️ Conflict Resolution Details:")
        for group in analysis['groups']:
            print(f"  Group {group['group_id']}: {group['candidates']} candidates")
            print(f"    ✅ Selected: {group['selected']['pattern']} - {group['selected']['text']!r}")
            print(f"       (Priority: {group['selected']['priority']}, Length: {group['selected']['length']})")
            for rejected in group['rejected']:
                print(f"    ❌ Rejected: {rejected['pattern']} - {rejected['text']!r}")
                print(f"       (Reason: {rejected['reason']})")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 3: 겹침 통계 분석
    print("🔍 Test Case 3: Overlap Statistics")
    stats = patterns.get_overlap_stats(complex_text)
    
    print("📈 Summary Statistics:")
    for key, value in stats['summary'].items():
        if isinstance(value, float):
            print(f"  - {key}: {value:.3f}")
        else:
            print(f"  - {key}: {value}")
    
    print("\n📊 Pattern Performance:")
    for pattern, data in stats['pattern_statistics'].items():
        selection_rate = data['selected'] / data['total'] if data['total'] > 0 else 0
        print(f"  - {pattern}: {data['selected']}/{data['total']} ({selection_rate:.1%})")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 4: 극단적 충돌 시나리오
    print("🔍 Test Case 4: Extreme Conflict Scenario")
    extreme_text = "arn:aws:lambda:us-east-1:123456789012:function:TestFunc with account 123456789012 and access key AKIA123456789012ABCD"
    
    print("🔄 Raw matches (no conflict resolution):")
    raw_extreme = patterns.find_matches(extreme_text, resolve_conflicts=False)
    for match in raw_extreme:
        pos = f"{match['start']}-{match['end']}"
        print(f"  - {match['pattern_name']}: {match['match']!r} at {pos} (p{match['pattern_def'].priority})")
    
    print("\n✅ Resolved matches:")
    resolved_extreme = patterns.find_matches(extreme_text, resolve_conflicts=True)
    for match in resolved_extreme:
        pos = f"{match['start']}-{match['end']}"
        print(f"  - {match['pattern_name']}: {match['match']!r} at {pos} (p{match['pattern_def'].priority})")
    
    efficiency = len(resolved_extreme) / len(raw_extreme) if raw_extreme else 1.0
    print(f"\n📊 Efficiency: {len(resolved_extreme)}/{len(raw_extreme)} = {efficiency:.1%}")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 5: 성능 벤치마크
    print("🔍 Test Case 5: Performance Benchmark")
    import time
    
    # 대용량 텍스트 생성
    large_text = "\n".join([
        f"Resource {i}: arn:aws:lambda:us-east-1:12345678901{i%10}:function:Func{i} in account 12345678901{i%10}"
        for i in range(100)
    ])
    
    # 성능 측정
    start_time = time.perf_counter()
    large_resolved = patterns.find_matches(large_text, resolve_conflicts=True)
    end_time = time.perf_counter()
    
    processing_time = end_time - start_time
    print(f"⏱️ Processing Time: {processing_time:.3f}s for {len(large_text)} chars")
    print(f"📊 Results: {len(large_resolved)} final matches")
    print(f"🚀 Performance: {len(large_text)/processing_time:.0f} chars/second")
    
    # 성능 요구사항 검증
    if processing_time < 2.0:
        print("✅ Performance requirement met: < 2.0s")
    else:
        print(f"⚠️ Performance warning: {processing_time:.3f}s > 2.0s")


if __name__ == "__main__":
    test_overlap_detection()
    print("🎉 Overlap Detection Engine validation complete!")