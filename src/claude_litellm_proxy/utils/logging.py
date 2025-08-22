"""
로깅 설정 유틸리티

TDD Green Phase: 구조화된 로깅 시스템
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    구조화된 로거 설정
    
    Args:
        name: 로거 이름 (보통 __name__)
        level: 로깅 레벨
        format_string: 커스텀 포맷 (선택)
        
    Returns:
        설정된 로거
    """
    logger = logging.getLogger(name)
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 로깅 레벨 설정
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # 핸들러 생성
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    
    # 포맷터 설정
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(handler)
    
    # 상위 로거로 전파 방지
    logger.propagate = False
    
    return logger