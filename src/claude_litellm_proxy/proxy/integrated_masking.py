"""
통합 마스킹 시스템

마스킹 엔진 + Redis 저장소를 통합하여
일관된 민감정보 추상화 제공

TDD Green Phase: 테스트를 통과하는 구현
"""

from typing import Dict, Tuple, Optional
from ..patterns.masking_engine import MaskingEngine
from .mapping_store import MappingStore


class IntegratedMaskingSystem:
    """
    통합 마스킹 시스템
    
    기능:
    - 마스킹 엔진과 Redis 저장소 통합
    - 일관된 마스킹 결과 보장
    - 영속적 매핑 관리
    - 세션 간 일관성 유지
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None
    ) -> None:
        """
        통합 시스템 초기화
        
        Args:
            redis_host: Redis 서버 호스트
            redis_port: Redis 서버 포트  
            redis_db: Redis 데이터베이스 번호
            redis_password: Redis 비밀번호 (선택)
        """
        # 마스킹 엔진 초기화
        self.masking_engine = MaskingEngine()
        
        # Redis 매핑 저장소 초기화
        self.mapping_store = MappingStore(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password
        )
    
    async def mask_text(self, text: str, ttl: Optional[int] = None) -> Tuple[str, Dict[str, str]]:
        """
        텍스트 마스킹 (Redis 기반 영속성)
        
        Args:
            text: 마스킹할 텍스트
            ttl: 매핑 만료 시간 (초, 선택사항)
            
        Returns:
            (마스킹된_텍스트, 매핑_정보)
        """
        if not text:
            return text or "", {}
        
        # 1. 기존 매핑이 있는지 Redis에서 확인
        existing_mappings = await self._get_existing_mappings_for_text(text)
        
        # 2. 마스킹 엔진으로 처리
        masked_text, new_mappings = self.masking_engine.mask_text(text)
        
        # 3. 새로운 매핑만 Redis에 저장
        mappings_to_save = {}
        final_mappings = {}
        
        for masked_val, original_val in new_mappings.items():
            # 기존 매핑이 있으면 재사용
            existing_masked = await self.mapping_store.get_masked(original_val)
            if existing_masked:
                # 텍스트에서 새 마스킹 값을 기존 값으로 교체
                masked_text = masked_text.replace(masked_val, existing_masked)
                final_mappings[existing_masked] = original_val
            else:
                # 새로운 매핑 저장 필요
                mappings_to_save[masked_val] = original_val
                final_mappings[masked_val] = original_val
        
        # 4. 새로운 매핑 Redis에 저장
        if mappings_to_save:
            await self.mapping_store.save_batch(mappings_to_save, ttl=ttl)
        
        return masked_text, final_mappings
    
    async def unmask_text(self, masked_text: str) -> str:
        """
        마스킹된 텍스트를 원본으로 복원
        
        Args:
            masked_text: 마스킹된 텍스트
            
        Returns:
            복원된 텍스트
        """
        if not masked_text:
            return masked_text or ""
        
        # Redis에서 매핑 정보 조회하여 복원
        unmasked_text = masked_text
        
        # 마스킹 패턴 찾기 (간단한 구현)
        words = masked_text.split()
        
        for word in words:
            # 구두점 제거하여 정확한 매칭
            clean_word = word.strip('.,!?:;"')
            
            # Redis에서 원본 값 조회
            original = await self.mapping_store.get_original(clean_word)
            if original:
                unmasked_text = unmasked_text.replace(clean_word, original)
        
        return unmasked_text
    
    async def get_original_from_redis(self, masked: str) -> Optional[str]:
        """Redis에서 직접 원본 값 조회 (테스트용)"""
        return await self.mapping_store.get_original(masked)
    
    async def clear_all_mappings(self) -> None:
        """모든 매핑 데이터 삭제 (테스트용)"""
        await self.mapping_store.clear_all()
        self.masking_engine.clear_mappings()
    
    async def close(self) -> None:
        """시스템 종료"""
        await self.mapping_store.close()
    
    async def _get_existing_mappings_for_text(self, text: str) -> Dict[str, str]:
        """
        텍스트에 포함된 리소스의 기존 매핑 조회
        
        Args:
            text: 검사할 텍스트
            
        Returns:
            기존 매핑 정보
        """
        existing_mappings = {}
        
        # 패턴으로 AWS 리소스 찾기
        matches = self.masking_engine.patterns.find_matches(text)
        
        for match in matches:
            original = match["match"]
            # Redis에서 기존 매핑 확인
            existing_masked = await self.mapping_store.get_masked(original)
            if existing_masked:
                existing_mappings[existing_masked] = original
        
        return existing_mappings