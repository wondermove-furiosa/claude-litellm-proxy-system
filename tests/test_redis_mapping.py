"""
Redis 매핑 저장소 TDD 테스트
실제 Redis 연결 필요, Mock 절대 금지

IMPORTANT: 이 테스트는 실제 Redis 서버가 실행되어야 함
docker run -d -p 6379:6379 redis:7-alpine
"""

import asyncio
import pytest
from typing import Dict, Optional

# Red Phase: 아직 구현되지 않은 모듈
try:
    from claude_litellm_proxy.proxy.mapping_store import MappingStore
except ImportError:
    MappingStore = None


class TestRedisMappingStore:
    """Redis 매핑 저장소 TDD 테스트"""

    @pytest.fixture(autouse=True)
    async def setup_store(self):
        """각 테스트 전 Redis 연결 설정"""
        if MappingStore is None:
            pytest.skip("MappingStore 모듈이 아직 구현되지 않음 (Red Phase)")
        
        # 실제 Redis 연결 (Mock 금지)
        self.store = MappingStore(
            host="localhost",
            port=6379,
            db=15  # 테스트용 DB
        )
        
        # 테스트 전 초기화
        await self.store.clear_all()
        
        yield  # 테스트 실행
        
        # 정리
        if hasattr(self, 'store'):
            await self.store.clear_all()
            await self.store.close()

    # Red Phase Test 1: 기본 저장/조회
    @pytest.mark.asyncio
    async def test_save_and_get_mapping(self):
        """기본 매핑 저장 및 조회 테스트"""
        # 실제 AWS 리소스 매핑
        original = "AKIA1234567890ABCDEF"
        masked = "iam-001"
        
        # Red: 저장 기능 구현 전 실패 예상
        await self.store.save_mapping(masked, original)
        
        # Green: 조회 기능 정상 작동해야 함
        retrieved = await self.store.get_original(masked)
        assert retrieved == original
        
        # 역방향 조회도 가능해야 함
        masked_back = await self.store.get_masked(original)
        assert masked_back == masked

    # Red Phase Test 2: TTL (Time To Live) 기능
    @pytest.mark.asyncio
    async def test_mapping_ttl(self):
        """매핑 만료 시간 기능 테스트"""
        original = "i-1234567890abcdef0"
        masked = "ec2-001"
        ttl_seconds = 2  # 2초 후 만료
        
        # Red: TTL 기능 구현 전 실패 예상
        await self.store.save_mapping(masked, original, ttl=ttl_seconds)
        
        # 즉시 조회는 성공해야 함
        retrieved = await self.store.get_original(masked)
        assert retrieved == original
        
        # TTL 후 조회는 None 반환해야 함
        await asyncio.sleep(ttl_seconds + 0.5)
        expired = await self.store.get_original(masked)
        assert expired is None

    # Red Phase Test 3: 배치 저장/조회
    @pytest.mark.asyncio
    async def test_batch_operations(self):
        """여러 매핑을 한번에 저장/조회하는 배치 기능"""
        mappings = {
            "ec2-001": "i-1234567890abcdef0",
            "vpc-001": "vpc-12345678", 
            "sg-001": "sg-87654321",
            "iam-001": "AKIA1234567890ABCDEF",
            "bucket-001": "my-prod-data-bucket"
        }
        
        # Red: 배치 저장 기능 구현 전 실패 예상
        await self.store.save_batch(mappings)
        
        # Green: 모든 매핑이 정상 저장되어야 함
        for masked, original in mappings.items():
            retrieved = await self.store.get_original(masked)
            assert retrieved == original

    # Red Phase Test 4: 중복 저장 처리
    @pytest.mark.asyncio
    async def test_duplicate_mapping_handling(self):
        """같은 원본에 대한 중복 저장 처리"""
        original = "AKIA1234567890ABCDEF" 
        masked1 = "iam-001"
        masked2 = "iam-002"
        
        # 첫 번째 저장
        await self.store.save_mapping(masked1, original)
        
        # 같은 원본을 다른 마스킹으로 저장 시도
        await self.store.save_mapping(masked2, original)
        
        # 최신 매핑이 유지되어야 함 (또는 첫 번째 유지 - 정책에 따라)
        latest_masked = await self.store.get_masked(original)
        assert latest_masked in [masked1, masked2]  # 정책에 따라 결정

    # Red Phase Test 5: 존재하지 않는 키 조회
    @pytest.mark.asyncio
    async def test_nonexistent_key_retrieval(self):
        """존재하지 않는 키 조회 시 안전한 처리"""
        # 존재하지 않는 키들
        nonexistent_keys = [
            "nonexistent-001",
            "fake-key",
            "",
            None
        ]
        
        for key in nonexistent_keys:
            if key is None:
                continue  # None은 건너뛰기
                
            # Red: 존재하지 않는 키 조회 시 None 반환해야 함
            result = await self.store.get_original(key)
            assert result is None

    # Red Phase Test 6: Redis 연결 실패 처리
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self):
        """Redis 연결 실패 시 예외 처리"""
        # 잘못된 포트로 연결 시도
        with pytest.raises(Exception):  # 연결 예외 발생해야 함
            failed_store = MappingStore(
                host="localhost",
                port=9999,  # 존재하지 않는 포트
                db=0,
                timeout=1  # 빠른 타임아웃
            )
            await failed_store.save_mapping("test", "test")

    # Red Phase Test 7: 대량 데이터 처리
    @pytest.mark.asyncio
    async def test_large_scale_mappings(self):
        """대량 데이터 처리 성능 테스트"""
        # 1000개 매핑 생성
        large_mappings = {}
        for i in range(1000):
            masked = f"test-{i:04d}"
            original = f"original-value-{i:04d}"
            large_mappings[masked] = original
        
        # Red: 대량 저장 기능 구현 전 실패 예상
        await self.store.save_batch(large_mappings)
        
        # 샘플 검증 (전체 검증은 시간 소모)
        sample_keys = [f"test-{i:04d}" for i in [0, 100, 500, 999]]
        for key in sample_keys:
            retrieved = await self.store.get_original(key)
            expected = large_mappings[key]
            assert retrieved == expected

    # Red Phase Test 8: 매핑 통계 정보
    @pytest.mark.asyncio
    async def test_mapping_statistics(self):
        """매핑 통계 정보 조회 기능"""
        # 여러 타입의 매핑 저장
        test_mappings = {
            "ec2-001": "i-1234567890abcdef0",
            "ec2-002": "i-abcdef1234567890",
            "iam-001": "AKIA1234567890ABCDEF",
            "bucket-001": "my-test-bucket"
        }
        
        await self.store.save_batch(test_mappings)
        
        # Red: 통계 기능 구현 전 실패 예상
        stats = await self.store.get_statistics()
        
        # Green: 통계 정보 정확해야 함
        assert stats["total_count"] == 4
        assert stats["ec2_count"] == 2
        assert stats["iam_count"] == 1
        assert stats["bucket_count"] == 1


class TestRedisRealConnectionRequired:
    """실제 Redis 연결 필수 확인 테스트"""
    
    def test_redis_connection_requirement(self):
        """이 테스트 파일이 실제 Redis를 필요로 함을 확인"""
        import redis
        
        try:
            # 실제 Redis 연결 확인
            r = redis.Redis(host='localhost', port=6379, db=15, socket_timeout=1)
            r.ping()
            print("✅ Redis 연결 성공: 실제 테스트 가능")
        except (redis.ConnectionError, redis.TimeoutError):
            pytest.skip(
                "Redis 서버가 실행되지 않음. "
                "다음 명령으로 Redis 시작: docker run -d -p 6379:6379 redis:7-alpine"
            )


if __name__ == "__main__":
    print("🚨 TDD Red Phase: Redis 매핑 저장소 테스트")
    print("실제 Redis 서버 필요: docker run -d -p 6379:6379 redis:7-alpine")
    pytest.main([__file__, "-v"])