"""
Redis 기반 매핑 저장소

민감정보 매핑을 Redis에 영속 저장하여 일관된 추상화 제공
TDD Green Phase: 테스트를 통과하는 구현
"""

import asyncio
import json
from typing import Dict, Optional, Any
import redis.asyncio as redis


class MappingStore:
    """
    Redis 기반 민감정보 매핑 저장소
    
    기능:
    - 원본 → 마스킹 매핑 저장
    - TTL 기반 자동 만료
    - 배치 저장/조회
    - 통계 정보 제공
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        timeout: int = 5
    ) -> None:
        """
        Redis 연결 초기화
        
        Args:
            host: Redis 서버 호스트
            port: Redis 서버 포트
            db: Redis 데이터베이스 번호
            password: Redis 비밀번호 (선택)
            timeout: 연결 타임아웃 (초)
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.timeout = timeout
        
        # Redis 클라이언트 (lazy 초기화)
        self._redis: Optional[redis.Redis] = None
        
        # 키 접두어
        self.masked_to_original_prefix = "m2o:"  # masked → original
        self.original_to_masked_prefix = "o2m:"  # original → masked
        self.stats_key = "mapping_stats"
    
    async def _get_redis(self) -> redis.Redis:
        """Redis 클라이언트 가져오기 (lazy 초기화)"""
        if self._redis is None:
            self._redis = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                socket_timeout=self.timeout,
                decode_responses=True
            )
            
            # 연결 테스트
            try:
                await self._redis.ping()
            except Exception as e:
                raise ConnectionError(f"Redis 연결 실패: {e}")
        
        return self._redis
    
    async def save_mapping(
        self, 
        masked: str, 
        original: str, 
        ttl: Optional[int] = None
    ) -> None:
        """
        매핑 저장
        
        Args:
            masked: 마스킹된 값 (예: "iam-001")
            original: 원본 값 (예: "AKIA123...")
            ttl: 만료 시간 (초, 선택사항)
        """
        redis_client = await self._get_redis()
        
        # 양방향 매핑 저장
        masked_key = f"{self.masked_to_original_prefix}{masked}"
        original_key = f"{self.original_to_masked_prefix}{original}"
        
        # 파이프라인으로 원자성 보장
        pipe = redis_client.pipeline()
        
        if ttl:
            pipe.setex(masked_key, ttl, original)
            pipe.setex(original_key, ttl, masked)
        else:
            pipe.set(masked_key, original)
            pipe.set(original_key, masked)
        
        # 통계 업데이트
        await self._update_statistics(masked, increment=True)
        
        await pipe.execute()
    
    async def get_original(self, masked: str) -> Optional[str]:
        """
        마스킹된 값으로 원본 값 조회
        
        Args:
            masked: 마스킹된 값
            
        Returns:
            원본 값 또는 None
        """
        redis_client = await self._get_redis()
        masked_key = f"{self.masked_to_original_prefix}{masked}"
        
        result = await redis_client.get(masked_key)
        return result
    
    async def get_masked(self, original: str) -> Optional[str]:
        """
        원본 값으로 마스킹된 값 조회
        
        Args:
            original: 원본 값
            
        Returns:
            마스킹된 값 또는 None
        """
        redis_client = await self._get_redis()
        original_key = f"{self.original_to_masked_prefix}{original}"
        
        result = await redis_client.get(original_key)
        return result
    
    async def save_batch(self, mappings: Dict[str, str], ttl: Optional[int] = None) -> None:
        """
        여러 매핑을 한번에 저장
        
        Args:
            mappings: {마스킹된_값: 원본_값} 딕셔너리
            ttl: 만료 시간 (초, 선택사항)
        """
        redis_client = await self._get_redis()
        
        # 파이프라인으로 배치 저장
        pipe = redis_client.pipeline()
        
        for masked, original in mappings.items():
            masked_key = f"{self.masked_to_original_prefix}{masked}"
            original_key = f"{self.original_to_masked_prefix}{original}"
            
            if ttl:
                pipe.setex(masked_key, ttl, original)
                pipe.setex(original_key, ttl, masked)
            else:
                pipe.set(masked_key, original)
                pipe.set(original_key, masked)
        
        # 배치 통계 업데이트
        for masked in mappings.keys():
            await self._update_statistics(masked, increment=True)
        
        await pipe.execute()
    
    async def get_statistics(self) -> Dict[str, int]:
        """
        매핑 통계 정보 조회
        
        Returns:
            통계 정보 딕셔너리
        """
        redis_client = await self._get_redis()
        
        # 전체 키 수 조회
        masked_keys = await redis_client.keys(f"{self.masked_to_original_prefix}*")
        total_count = len(masked_keys)
        
        # 타입별 통계
        type_counts = {}
        for key in masked_keys:
            # 키에서 마스킹된 값 추출
            masked_value = key.replace(self.masked_to_original_prefix, "")
            
            # 타입 추출 (예: "ec2-001" → "ec2")
            if "-" in masked_value:
                resource_type = masked_value.split("-")[0]
                type_counts[f"{resource_type}_count"] = type_counts.get(f"{resource_type}_count", 0) + 1
        
        return {
            "total_count": total_count,
            **type_counts
        }
    
    async def clear_all(self) -> None:
        """모든 매핑 데이터 삭제 (테스트용)"""
        redis_client = await self._get_redis()
        
        # 모든 매핑 키 삭제
        masked_keys = await redis_client.keys(f"{self.masked_to_original_prefix}*")
        original_keys = await redis_client.keys(f"{self.original_to_masked_prefix}*")
        
        all_keys = masked_keys + original_keys + [self.stats_key]
        
        if all_keys:
            await redis_client.delete(*all_keys)
    
    async def close(self) -> None:
        """Redis 연결 종료"""
        if self._redis:
            await self._redis.aclose()
            self._redis = None
    
    async def _update_statistics(self, masked: str, increment: bool = True) -> None:
        """
        통계 정보 업데이트 (내부용)
        
        Args:
            masked: 마스킹된 값
            increment: 증가(True) 또는 감소(False)
        """
        # 현재는 get_statistics에서 실시간 계산
        # 필요시 Redis에 별도 통계 저장 가능
        pass