#!/usr/bin/env python3
"""
Redis 매핑 충돌 정리 스크립트

기존의 충돌하는 매핑들을 모두 제거하여 클린 상태로 만듭니다.
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 패스에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from claude_litellm_proxy.proxy.mapping_store import MappingStore


async def cleanup_redis_mappings():
    """Redis에서 모든 매핑과 카운터 정리"""
    
    print("🧹 Redis 매핑 충돌 정리 시작...")
    
    # MappingStore 초기화
    mapping_store = MappingStore(
        host="localhost",
        port=6379,
        db=0
    )
    
    try:
        # 1. 현재 상태 확인
        print("\n📊 정리 전 상태 확인:")
        redis_client = await mapping_store._get_redis()
        
        # 모든 매핑 키 조회
        masked_keys = await redis_client.keys("m2o:*")
        original_keys = await redis_client.keys("o2m:*")
        counter_keys = await redis_client.keys("counter:*")
        
        print(f"  - 마스킹→원본 매핑: {len(masked_keys)}개")
        print(f"  - 원본→마스킹 매핑: {len(original_keys)}개")
        print(f"  - 카운터: {len(counter_keys)}개")
        
        # 충돌 상황 확인
        print("\n🔍 충돌 매핑 확인:")
        conflicts = {}
        for key in masked_keys:
            masked_val = key.replace("m2o:", "")
            original_val = await redis_client.get(key)
            
            if masked_val in conflicts:
                conflicts[masked_val].append(original_val)
            else:
                conflicts[masked_val] = [original_val]
        
        conflict_count = 0
        for masked_val, original_list in conflicts.items():
            if len(original_list) > 1:
                conflict_count += 1
                print(f"  ⚠️ {masked_val} → {original_list}")
        
        print(f"  - 총 {conflict_count}개 충돌 발견")
        
        # 2. 모든 데이터 정리
        print("\n🗑️ 모든 매핑 데이터 정리 중...")
        await mapping_store.clear_all()
        
        # 추가로 카운터도 정리
        if counter_keys:
            await redis_client.delete(*counter_keys)
        
        print("✅ Redis 매핑 정리 완료!")
        
        # 3. 정리 후 상태 확인
        masked_keys_after = await redis_client.keys("m2o:*")
        original_keys_after = await redis_client.keys("o2m:*")
        counter_keys_after = await redis_client.keys("counter:*")
        
        print(f"\n📊 정리 후 상태:")
        print(f"  - 마스킹→원본 매핑: {len(masked_keys_after)}개")
        print(f"  - 원본→마스킹 매핑: {len(original_keys_after)}개")
        print(f"  - 카운터: {len(counter_keys_after)}개")
        
    except Exception as e:
        print(f"❌ Redis 정리 실패: {e}")
        return False
    
    finally:
        await mapping_store.close()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(cleanup_redis_mappings())
    
    if success:
        print("\n🎉 Redis 매핑 충돌 정리가 성공적으로 완료되었습니다!")
        print("이제 새로운 마스킹 테스트를 실행할 수 있습니다.")
    else:
        print("\n💥 Redis 정리 중 오류가 발생했습니다.")
        sys.exit(1)