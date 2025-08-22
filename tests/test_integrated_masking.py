"""
통합 마스킹 시스템 TDD 테스트
마스킹 엔진 + Redis 저장소 통합

실제 Redis 서버 필요, Mock 절대 금지
docker run -d -p 6379:6379 redis:7-alpine
"""

import pytest
from typing import Dict

# Red Phase: 통합 시스템 구현 전
try:
    from claude_litellm_proxy.patterns.masking_engine import MaskingEngine
    from claude_litellm_proxy.proxy.mapping_store import MappingStore
    from claude_litellm_proxy.proxy.integrated_masking import IntegratedMaskingSystem
except ImportError:
    MaskingEngine = None
    MappingStore = None
    IntegratedMaskingSystem = None


class TestIntegratedMasking:
    """통합 마스킹 시스템 TDD 테스트"""

    @pytest.fixture(autouse=True)
    async def setup_system(self):
        """통합 시스템 설정"""
        if IntegratedMaskingSystem is None:
            pytest.skip("IntegratedMaskingSystem 모듈이 아직 구현되지 않음 (Red Phase)")
        
        # 실제 Redis와 통합
        self.system = IntegratedMaskingSystem(
            redis_host="localhost",
            redis_port=6379,
            redis_db=15
        )
        
        await self.system.clear_all_mappings()
        
        yield
        
        # 정리
        if hasattr(self, 'system'):
            await self.system.clear_all_mappings()
            await self.system.close()

    @pytest.mark.asyncio
    async def test_persistent_masking(self):
        """영속적 마스킹 - Redis에 저장 후 재조회"""
        # 첫 번째 마스킹
        text1 = "Use IAM key AKIA1234567890ABCDEF for access"
        masked1, mapping1 = await self.system.mask_text(text1)
        
        # 같은 텍스트 다시 마스킹 - 동일한 결과여야 함
        masked2, mapping2 = await self.system.mask_text(text1)
        
        assert masked1 == masked2  # 일관된 마스킹
        assert mapping1 == mapping2  # 동일한 매핑
        
        # Redis에서 직접 확인
        for masked_val, original_val in mapping1.items():
            redis_original = await self.system.get_original_from_redis(masked_val)
            assert redis_original == original_val

    @pytest.mark.asyncio 
    async def test_cross_session_consistency(self):
        """세션 간 일관성 - 시스템 재시작 후에도 동일한 마스킹"""
        # 원본 텍스트
        original_text = "EC2 i-1234567890abcdef0 in VPC vpc-12345678"
        
        # 첫 번째 시스템에서 마스킹
        masked1, mapping1 = await self.system.mask_text(original_text)
        
        # 시스템 종료
        await self.system.close()
        
        # 새로운 시스템 생성 (Redis 데이터는 유지)
        new_system = IntegratedMaskingSystem(
            redis_host="localhost",
            redis_port=6379,
            redis_db=15
        )
        
        # 같은 텍스트 마스킹 - 동일한 결과여야 함
        masked2, mapping2 = await new_system.mask_text(original_text)
        
        assert masked1 == masked2
        assert mapping1 == mapping2
        
        await new_system.close()

    @pytest.mark.asyncio
    async def test_unmask_with_redis_mapping(self):
        """Redis 매핑을 사용한 언마스킹"""
        # 복잡한 텍스트 마스킹
        original_text = """
        Infrastructure setup:
        - EC2 instance: i-1234567890abcdef0
        - VPC: vpc-12345678  
        - Security Group: sg-87654321
        - IAM Key: AKIA1234567890ABCDEF
        - S3 Bucket: my-company-prod-logs
        """
        
        masked_text, mapping = await self.system.mask_text(original_text)
        
        # 언마스킹 수행
        unmasked_text = await self.system.unmask_text(masked_text)
        
        # 원본과 동일해야 함 (공백 차이 제외)
        original_resources = [
            "i-1234567890abcdef0",
            "vpc-12345678", 
            "sg-87654321",
            "AKIA1234567890ABCDEF",
            "my-company-prod-logs"
        ]
        
        for resource in original_resources:
            assert resource in unmasked_text

    @pytest.mark.asyncio
    async def test_ttl_integration(self):
        """TTL 통합 테스트 - 만료된 매핑 처리"""
        text = "Test with IAM key AKIATEST123456789012"
        
        # 짧은 TTL로 마스킹
        masked1, mapping1 = await self.system.mask_text(text, ttl=1)  # 1초 후 만료
        
        # 즉시 확인 - 정상 작동
        unmasked1 = await self.system.unmask_text(masked1)
        assert "AKIATEST123456789012" in unmasked1
        
        # TTL 대기
        import asyncio
        await asyncio.sleep(1.5)
        
        # 만료 후 언마스킹 시도 - 마스킹된 형태 그대로 반환
        unmasked2 = await self.system.unmask_text(masked1)
        # 만료되어 복원 불가 - 마스킹된 값 그대로 포함
        assert any(val in unmasked2 for val in mapping1.keys())

    @pytest.mark.asyncio
    async def test_large_text_performance(self):
        """대용량 텍스트 처리 성능 테스트"""
        # 큰 텍스트 생성 (다양한 AWS 리소스 포함)
        large_text = ""
        for i in range(100):
            large_text += f"""
            Server {i}:
            - EC2: i-{i:016x}a
            - VPC: vpc-{i:08x}
            - IAM: AKIA{i:016d}
            - Bucket: logs-{i:04d}-bucket
            """
        
        # 성능 측정
        import time
        start_time = time.time()
        
        masked_text, mapping = await self.system.mask_text(large_text)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 5초 이내 완료 (성능 요구사항)
        assert duration < 5.0, f"마스킹 시간 초과: {duration:.2f}초"
        
        # 모든 리소스가 마스킹되었는지 확인
        assert len(mapping) == 400  # 100 * 4 types

    @pytest.mark.asyncio
    async def test_concurrent_masking(self):
        """동시 마스킹 요청 처리 테스트"""
        import asyncio
        
        # 동시 요청 생성
        texts = [
            f"EC2 instance i-{i:016x}a with IAM AKIA{i:016d}"
            for i in range(10)
        ]
        
        # 동시 마스킹 실행
        tasks = [self.system.mask_text(text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        # 모든 요청이 성공했는지 확인
        assert len(results) == 10
        
        for masked_text, mapping in results:
            assert len(mapping) == 2  # EC2 + IAM
            assert masked_text != texts[results.index((masked_text, mapping))]

    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """오류 상황에서의 복구 테스트"""
        text = "Normal text with EC2 i-1234567890abcdef0"
        
        # 정상 마스킹
        masked1, mapping1 = await self.system.mask_text(text)
        
        # Redis 연결 일시적 중단 시뮬레이션은 어려우므로
        # 존재하지 않는 키로 언마스킹 시도
        fake_masked = "fake-001 instance in vpc-999"
        
        # 오류 없이 처리되어야 함 (원본 그대로 반환)
        result = await self.system.unmask_text(fake_masked)
        assert result == fake_masked


if __name__ == "__main__":
    print("🚨 TDD Red Phase: 통합 마스킹 시스템 테스트")
    print("실제 Redis 서버 필요: docker run -d -p 6379:6379 redis:7-alpine")
    pytest.main([__file__, "-v"])