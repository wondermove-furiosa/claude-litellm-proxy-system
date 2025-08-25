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
        # 마스킹 엔진 초기화 (mapping_store 주입)
        self.masking_engine = MaskingEngine(mapping_store=None)  # 일단 None으로 초기화
        
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
        if existing_mappings:
            print(f"[DEBUG] 기존 매핑 {len(existing_mappings)}개 발견: {existing_mappings}")
        
        # 2. Redis 기반 직접 마스킹 처리 (기존 매핑 활용)
        masked_text, final_mappings = await self._mask_text_with_redis_counter(text, existing_mappings)
        
        if final_mappings:
            print(f"[DEBUG] 최종 매핑 {len(final_mappings)}개 생성: {final_mappings}")
        
        # 매핑은 이미 _mask_text_with_redis_counter에서 저장됨
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
        
        print(f"[DEBUG] 언마스킹 대상 텍스트: {masked_text[:200]}...")
        
        # Redis에서 매핑 정보 조회하여 복원
        unmasked_text = masked_text
        
        # 정규식을 사용하여 AWS 마스킹 패턴 찾기
        import re
        aws_pattern = r'AWS_[A-Z_]+_\d{3}'
        matches = re.finditer(aws_pattern, masked_text)
        
        # 뒤에서부터 치환 (인덱스 변화 방지)
        replacements = []
        for match in matches:
            masked_token = match.group()
            start, end = match.span()
            replacements.append((start, end, masked_token))
        
        # 뒤에서부터 처리
        replacements.sort(key=lambda x: x[0], reverse=True)
        
        for start, end, masked_token in replacements:
            print(f"[DEBUG] 언마스킹 시도: '{masked_token}'")
            
            # Redis에서 원본 값 조회
            original = await self.mapping_store.get_original(masked_token)
            if original:
                print(f"[DEBUG] 언마스킹 성공: {masked_token} -> {original}")
                unmasked_text = unmasked_text[:start] + original + unmasked_text[end:]
            else:
                print(f"[DEBUG] 언마스킹 실패: {masked_token} (Redis에서 찾을 수 없음)")
        
        return unmasked_text
    
    async def _mask_text_with_redis_counter(self, text: str, existing_mappings: Optional[Dict[str, str]] = None) -> tuple[str, Dict[str, str]]:
        """
        Redis 기반 유일 카운터를 사용한 마스킹
        
        Args:
            text: 마스킹할 텍스트
            existing_mappings: 기존 매핑 정보 (중복 Redis 조회 방지)
            
        Returns:
            (마스킹된_텍스트, 매핑_정보)
        """
        if not text:
            return text or "", {}
        
        # 1. AWS 패턴 찾기
        matches = self.masking_engine.patterns.find_matches(text)
        if not matches:
            return text, {}
        
        masked_text = text
        mappings = {}
        
        # 뒤에서부터 처리 (인덱스 변화 방지)
        matches.sort(key=lambda x: x["start"], reverse=True)
        
        for match in matches:
            original = match["match"]
            pattern_def = match["pattern_def"]
            print(f"[DEBUG] 처리 중인 원본: {original} (타입: {pattern_def.type})")
            
            # 2. 기존 매핑 확인 (existing_mappings 우선 사용)
            existing_masked = None
            if existing_mappings:
                # 기존 매핑에서 찾기
                for masked_key, original_val in existing_mappings.items():
                    if original_val == original:
                        existing_masked = masked_key
                        print(f"[DEBUG] 기존 매핑에서 발견: {original} → {existing_masked}")
                        break
            
            # 기존 매핑에 없으면 Redis에서 직접 조회
            if not existing_masked:
                existing_masked = await self.mapping_store.get_masked(original)
                if existing_masked:
                    print(f"[DEBUG] Redis에서 발견: {original} → {existing_masked}")
            
            if existing_masked:
                # 기존 매핑 재사용
                masked_value = existing_masked
                mappings[masked_value] = original
                print(f"[DEBUG] 기존 매핑 재사용: {original} → {masked_value}")
            else:
                # 3. Redis 기반 유일 카운터로 새 ID 생성
                counter_value = await self.mapping_store.get_next_counter(pattern_def.type)
                print(f"[DEBUG] 새 카운터 생성: {pattern_def.type} → {counter_value}")
                
                # 4. 마스킹 값 생성
                try:
                    masked_value = pattern_def.replacement.format(counter_value)
                except (ValueError, KeyError):
                    masked_value = f"{pattern_def.type.upper()}_{counter_value:03d}"
                
                print(f"[DEBUG] 새 매핑 생성: {original} → {masked_value}")
                
                # 5. Redis에 매핑 저장
                await self.mapping_store.save_mapping(masked_value, original)
                mappings[masked_value] = original
            
            # 6. 텍스트에서 교체
            start, end = match["start"], match["end"]
            masked_text = masked_text[:start] + masked_value + masked_text[end:]
        
        return masked_text, mappings
    
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