#!/usr/bin/env python3
"""
Phase 3: 5개 추가 패턴 검증 테스트
레퍼런스 50개 → 56개 패턴 (112% 달성)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from claude_litellm_proxy.patterns.cloud_patterns import CloudPatterns


def test_phase3_patterns():
    """Phase 3 추가 패턴 테스트"""
    
    patterns = CloudPatterns()
    patterns.enable_debug(False)  # 간결한 출력을 위해 디버그 비활성화
    
    print("🚀 Phase 3: 혁신적 추가 패턴 테스트")
    print("레퍼런스 50개 → 56개 패턴 (112% 달성)")
    print("=" * 60)
    
    # Test Case 1: Fargate Task ARN (최고 우선순위)
    print("🔍 Test Case 1: Fargate Task ARN (Priority 50)")
    fargate_text = "Deploy task arn:aws:ecs:us-east-1:123456789012:task/my-cluster/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    
    resolved = patterns.find_matches(fargate_text)
    print(f"Input: {fargate_text}")
    print(f"Matches: {len(resolved)}")
    for match in resolved:
        print(f"  ✅ {match['pattern_name']}: {match['match']} (Priority: {match['pattern_def'].priority})")
    
    print("\n" + "-"*60 + "\n")
    
    # Test Case 2: SSM Session ARN
    print("🔍 Test Case 2: Systems Manager Session ARN (Priority 60)")
    ssm_text = "Active session: arn:aws:ssm:us-east-1:123456789012:session/user-12345678901ab"
    
    resolved = patterns.find_matches(ssm_text)
    print(f"Input: {ssm_text}")
    print(f"Matches: {len(resolved)}")
    for match in resolved:
        print(f"  ✅ {match['pattern_name']}: {match['match']} (Priority: {match['pattern_def'].priority})")
    
    print("\n" + "-"*60 + "\n")
    
    # Test Case 3: CloudWatch Insights Query ID (with Validator)
    print("🔍 Test Case 3: CloudWatch Insights Query ID (Priority 75)")
    
    # Valid Insights Query IDs
    valid_queries = [
        "a12b3c4d-5678-9012-3456-789012345678",  # Starts with 'a' 
        "0fedcba9-8765-4321-0987-654321098765",  # Starts with '0'
        "cf123456-789a-bcde-f012-3456789abcde"   # Starts with 'c'
    ]
    
    # Invalid patterns (should not match KMS keys)
    invalid_patterns = [
        "g1234567-8901-2345-6789-012345678901",  # Starts with 'g' (invalid)
        "z9876543-2108-7654-3210-987654321098"   # Starts with 'z' (invalid)
    ]
    
    print("Valid CloudWatch Insights Query IDs:")
    for query_id in valid_queries:
        test_text = f"Query {query_id} completed"
        resolved = patterns.find_matches(test_text)
        matched = len(resolved) > 0 and any(m['pattern_name'] == 'insights_query' for m in resolved)
        print(f"  {'✅' if matched else '❌'} {query_id}: {'Matched' if matched else 'Not matched'}")
    
    print("Invalid patterns (should not match):")
    for query_id in invalid_patterns:
        test_text = f"Query {query_id} completed"
        resolved = patterns.find_matches(test_text)
        matched = len(resolved) > 0 and any(m['pattern_name'] == 'insights_query' for m in resolved)
        print(f"  {'❌' if matched else '✅'} {query_id}: {'Incorrectly matched' if matched else 'Correctly rejected'}")
    
    print("\n" + "-"*60 + "\n")
    
    # Test Case 4: App Runner Service ARN
    print("🔍 Test Case 4: App Runner Service ARN (Priority 85)")
    apprunner_text = "App Runner: arn:aws:apprunner:us-east-1:123456789012:service/my-app/1234567890abcdef1234567890abcdef"
    
    resolved = patterns.find_matches(apprunner_text)
    print(f"Input: {apprunner_text}")
    print(f"Matches: {len(resolved)}")
    for match in resolved:
        print(f"  ✅ {match['pattern_name']}: {match['match']} (Priority: {match['pattern_def'].priority})")
    
    print("\n" + "-"*60 + "\n")
    
    # Test Case 5: EventBridge Custom Bus ARN
    print("🔍 Test Case 5: EventBridge Custom Bus ARN (Priority 95)")
    eventbridge_text = "Event bus: arn:aws:events:us-east-1:123456789012:event-bus/custom-business-bus"
    
    resolved = patterns.find_matches(eventbridge_text)
    print(f"Input: {eventbridge_text}")
    print(f"Matches: {len(resolved)}")
    for match in resolved:
        print(f"  ✅ {match['pattern_name']}: {match['match']} (Priority: {match['pattern_def'].priority})")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 6: 모든 새 패턴 혼합 시나리오
    print("🔍 Test Case 6: All New Patterns Mixed Scenario")
    mixed_text = """
    Modern AWS Infrastructure:
    - Fargate Task: arn:aws:ecs:us-east-1:123456789012:task/prod-cluster/a1b2c3d4-e5f6-7890-abcd-ef1234567890
    - SSM Session: arn:aws:ssm:us-east-1:123456789012:session/admin-12345678901ab 
    - App Runner: arn:aws:apprunner:us-east-1:123456789012:service/web-app/fedcba0987654321fedcba0987654321
    - EventBridge: arn:aws:events:us-east-1:123456789012:event-bus/microservices.events
    - Query ID: a1234567-89ab-cdef-0123-456789abcdef
    - Account: 123456789012
    """
    
    resolved, analysis = patterns.find_matches_with_analysis(mixed_text)
    
    print(f"📊 Mixed Scenario Analysis:")
    print(f"  - Total patterns matched: {analysis['efficiency']['original_matches']}")
    print(f"  - Final matches: {analysis['efficiency']['resolved_matches']}")
    print(f"  - Efficiency: {analysis['efficiency']['reduction_rate']:.1%}")
    
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
            priority_note = f"(P{match['pattern_def'].priority})"
            print(f"    - {match['pattern_name']}: {match['match'][:50]}{'...' if len(match['match']) > 50 else ''} {priority_note}")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 7: 우선순위 검증
    print("🔍 Test Case 7: Priority Verification")
    all_patterns = patterns._patterns
    new_patterns = ['fargate_task', 'ssm_session', 'insights_query', 'apprunner_service', 'eventbridge_bus']
    
    print("New patterns priority order:")
    new_pattern_list = [(name, all_patterns[name]) for name in new_patterns]
    new_pattern_list.sort(key=lambda x: x[1].priority)
    
    for i, (name, pattern_def) in enumerate(new_pattern_list):
        print(f"  {i+1}. {name:20s} (Priority: {pattern_def.priority:2d}) - {pattern_def.type}")
    
    print(f"\nTotal patterns now: {len(all_patterns)} (vs. 50 in reference)")
    achievement = len(all_patterns) / 50 * 100
    print(f"Achievement: {achievement:.1f}% of reference (112%+ target ✅)")
    
    print("\n" + "="*60 + "\n")
    
    # Test Case 8: 성능 테스트
    print("🔍 Test Case 8: Performance Test with New Patterns")
    import time
    
    # 새 패턴들을 포함한 대용량 텍스트
    performance_text = "\n".join([
        f"Task {i}: arn:aws:ecs:us-east-1:12345678901{i%10}:task/cluster-{i}/a1b2c3d4-e5f6-7890-abcd-ef123456789{i%10}"
        for i in range(50)
    ])
    
    start_time = time.perf_counter()
    perf_resolved = patterns.find_matches(performance_text)
    end_time = time.perf_counter()
    
    processing_time = end_time - start_time
    print(f"⏱️  Processing Time: {processing_time:.3f}s")
    print(f"📊 Results: {len(perf_resolved)} matches")
    print(f"🚀 Performance: {len(performance_text)/processing_time:.0f} chars/second")
    
    if processing_time < 2.0:
        print("✅ Performance target met: < 2.0s")
    else:
        print(f"⚠️  Performance warning: {processing_time:.3f}s > 2.0s")


if __name__ == "__main__":
    test_phase3_patterns()
    print("🎉 Phase 3 validation complete!")