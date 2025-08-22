"""
마스킹 엔진 - 핵심 민감정보 마스킹 기능

TDD Green Phase: 테스트를 통과하는 최소한의 구현
ref-1 Kong 플러그인의 마스킹 로직을 Python으로 포팅
"""

from typing import Dict, List, Optional, Tuple, Any

from .cloud_patterns import CloudPatterns, PatternDefinition


class MaskingEngine:
    """
    AWS 리소스 마스킹 엔진

    민감정보를 추상화된 형태로 변환하고 매핑 정보를 관리
    예: AKIA1234567890ABCDEF → iam-01
    """

    def __init__(self) -> None:
        """마스킹 엔진 초기화"""
        self.patterns = CloudPatterns()
        self._counter: Dict[str, int] = {}  # 각 타입별 카운터
        self._mapping_cache: Dict[str, str] = {}  # 원본 → 마스킹 매핑
        self._reverse_mapping: Dict[str, str] = {}  # 마스킹 → 원본 매핑

    def mask_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        텍스트의 AWS 리소스를 마스킹

        Args:
            text: 마스킹할 텍스트

        Returns:
            (마스킹된_텍스트, 매핑_정보)
            매핑_정보: {마스킹된_값: 원본_값}
        """
        # TDD Green Phase: 빈 텍스트나 None 처리
        if not text:
            return text or "", {}

        if not isinstance(text, str):
            return str(text), {}

        # AWS 리소스 찾기
        matches = self.patterns.find_matches(text)

        if not matches:
            # AWS 리소스가 없으면 원본 그대로 반환
            return text, {}

        # 마스킹 수행
        masked_text = text
        mapping = {}

        # 뒤에서부터 처리 (인덱스 변화 방지)
        matches.sort(key=lambda x: x["start"], reverse=True)

        for match in matches:
            original = match["match"]
            pattern_def = match["pattern_def"]

            # 이미 마스킹된 값이 있으면 재사용
            if original in self._mapping_cache:
                masked_value = self._mapping_cache[original]
            else:
                # 새로운 마스킹 값 생성
                masked_value = self._generate_masked_value(original, pattern_def)
                self._mapping_cache[original] = masked_value
                self._reverse_mapping[masked_value] = original

            # 텍스트에서 교체
            start, end = match["start"], match["end"]
            masked_text = masked_text[:start] + masked_value + masked_text[end:]

            # 매핑 정보 추가
            mapping[masked_value] = original

        return masked_text, mapping

    def _generate_masked_value(self, original: str, pattern_def: PatternDefinition) -> str:
        """
        원본 값에 대한 마스킹된 값 생성

        Args:
            original: 원본 값
            pattern_def: 패턴 정의

        Returns:
            마스킹된 값 (예: "iam-01")
        """
        # 타입별 카운터 증가
        resource_type = pattern_def.type
        if resource_type not in self._counter:
            self._counter[resource_type] = 0

        self._counter[resource_type] += 1
        counter_value = self._counter[resource_type]

        # 마스킹 값 생성
        try:
            masked_value = pattern_def.replacement.format(counter_value)
        except (ValueError, KeyError):
            # 포맷 문제가 있으면 기본 형식 사용
            masked_value = f"{resource_type}-{counter_value:03d}"

        return masked_value

    def unmask_text(self, masked_text: str, mapping: Dict[str, str]) -> str:
        """
        마스킹된 텍스트를 원본으로 복원

        Args:
            masked_text: 마스킹된 텍스트
            mapping: 매핑 정보 {마스킹된_값: 원본_값}

        Returns:
            복원된 텍스트
        """
        if not masked_text or not mapping:
            return masked_text or ""

        unmasked_text = masked_text

        # 매핑 정보로 복원
        for masked_value, original_value in mapping.items():
            unmasked_text = unmasked_text.replace(masked_value, original_value)

        return unmasked_text

    def get_mapping_info(self) -> Dict[str, str]:
        """현재 매핑 정보 반환"""
        return self._reverse_mapping.copy()

    def clear_mappings(self) -> None:
        """매핑 정보 초기화"""
        self._counter.clear()
        self._mapping_cache.clear()
        self._reverse_mapping.clear()

    def get_statistics(self) -> Dict[str, int]:
        """마스킹 통계 정보 반환"""
        return self._counter.copy()
