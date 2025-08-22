"""
LiteLLM 클라이언트 통합

실제 LiteLLM을 통해 Claude API 호출 처리
TDD Green Phase: 실제 LLM 프록시 구현
"""

import os
import asyncio
from typing import Dict, Any, Optional
import litellm
from ..utils.logging import setup_logger

# 로거 설정
logger = setup_logger(__name__)


class LiteLLMClient:
    """
    LiteLLM 클라이언트
    
    기능:
    - Claude API 호출 프록시
    - 모델 설정 관리
    - 에러 처리 및 재시도
    - 비용 및 사용량 추적
    """
    
    def __init__(self):
        """LiteLLM 클라이언트 초기화"""
        # Claude API 키 설정
        self.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.claude_api_key:
            logger.warning("ANTHROPIC_API_KEY 환경변수가 설정되지 않음")
        else:
            logger.info(f"API 키 확인: ...{self.claude_api_key[-10:] if len(self.claude_api_key) > 10 else 'short'}")
        
        # LiteLLM 전용 Claude API 주소 설정
        self.claude_base_url = os.getenv("LITELLM_CLAUDE_BASE_URL", "https://api.anthropic.com")
        logger.info(f"LiteLLM Claude API 주소: {self.claude_base_url}")
        
        # LiteLLM 기본 설정
        litellm.set_verbose = True   # 디버깅을 위해 True로 설정
        litellm.drop_params = True   # 모델이 지원하지 않는 파라미터 자동 제거
        
        # 기본 모델 설정
        self.default_model = "claude-3-haiku-20240307"
        
        logger.info("LiteLLM 클라이언트 초기화 완료")
    
    async def call_claude_api(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Claude API 호출 (비동기)
        
        Args:
            request_data: Claude API 요청 데이터
            
        Returns:
            Claude API 응답 데이터
            
        Raises:
            Exception: API 호출 실패시
        """
        try:
            # 모델 설정 (기본값 적용)
            model = request_data.get("model", self.default_model)
            
            # Claude API 형식으로 변환
            max_tokens = min(request_data.get("max_tokens", 4096), 4096)  # Haiku 모델 제한
            litellm_request = {
                "model": model,
                "messages": request_data.get("messages", []),
                "max_tokens": max_tokens,
                "temperature": request_data.get("temperature", 0.7),
                "api_key": self.claude_api_key,
                "base_url": self.claude_base_url  # 환경변수에서 읽은 Claude API 주소
            }
            
            # 추가 파라미터 처리
            if "system" in request_data:
                litellm_request["system"] = request_data["system"]
            
            if "stop_sequences" in request_data:
                litellm_request["stop"] = request_data["stop_sequences"]
            
            logger.info(f"Claude API 호출 시작: model={model}")
            
            # LiteLLM을 통한 비동기 API 호출
            response = await litellm.acompletion(**litellm_request)
            
            # 응답 형식 변환 (Claude API 형식으로)
            claude_response = self._convert_to_claude_format(response)
            
            logger.info("Claude API 호출 성공")
            return claude_response
            
        except Exception as e:
            logger.error(f"Claude API 호출 실패: {e}")
            raise
    
    def _convert_to_claude_format(self, litellm_response: Any) -> Dict[str, Any]:
        """
        LiteLLM 응답을 Claude API 형식으로 변환
        
        Args:
            litellm_response: LiteLLM 응답 객체
            
        Returns:
            Claude API 형식 응답
        """
        try:
            # LiteLLM 응답에서 필요한 정보 추출
            choice = litellm_response.choices[0]
            message = choice.message
            
            # Claude API 형식으로 변환
            claude_response = {
                "content": [
                    {
                        "type": "text",
                        "text": message.content
                    }
                ],
                "model": litellm_response.model,
                "role": "assistant",
                "stop_reason": self._map_finish_reason(choice.finish_reason),
                "usage": {
                    "input_tokens": litellm_response.usage.prompt_tokens,
                    "output_tokens": litellm_response.usage.completion_tokens
                }
            }
            
            return claude_response
            
        except Exception as e:
            logger.error(f"응답 형식 변환 실패: {e}")
            raise
    
    def _map_finish_reason(self, finish_reason: Optional[str]) -> str:
        """
        LiteLLM finish_reason을 Claude API 형식으로 매핑
        
        Args:
            finish_reason: LiteLLM finish_reason
            
        Returns:
            Claude API stop_reason
        """
        mapping = {
            "stop": "end_turn",
            "length": "max_tokens",
            "content_filter": "stop_sequence",
            None: "end_turn"
        }
        
        return mapping.get(finish_reason, "end_turn")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        LiteLLM 연결 상태 확인
        
        Returns:
            상태 정보
        """
        try:
            # 간단한 테스트 호출
            test_request = {
                "model": self.default_model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10,
                "api_key": self.claude_api_key,
                "base_url": self.claude_base_url  # 환경변수에서 읽은 Claude API 주소
            }
            
            # 타임아웃을 짧게 설정한 테스트 호출
            response = await asyncio.wait_for(
                litellm.acompletion(**test_request),
                timeout=10.0
            )
            
            return {
                "status": "healthy",
                "model": self.default_model,
                "api_key_configured": bool(self.claude_api_key)
            }
            
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "model": self.default_model,
                "api_key_configured": bool(self.claude_api_key)
            }
        except Exception as e:
            logger.error(f"LiteLLM 헬스체크 실패: {e}")
            return {
                "status": "error",
                "error": str(e),
                "model": self.default_model,
                "api_key_configured": bool(self.claude_api_key)
            }