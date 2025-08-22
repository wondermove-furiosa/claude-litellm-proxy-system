"""
LiteLLM 클라이언트 테스트

실제 LiteLLM 클라이언트 기능 검증
TDD Green Phase: 실제 통합 테스트
"""

import pytest
import os
from unittest.mock import patch, AsyncMock
from claude_litellm_proxy.proxy.litellm_client import LiteLLMClient


class TestLiteLLMClient:
    """LiteLLM 클라이언트 테스트"""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """테스트 설정 및 정리"""
        # 환경변수 백업
        self.original_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        yield
        
        # 환경변수 복원
        if self.original_api_key:
            os.environ["ANTHROPIC_API_KEY"] = self.original_api_key
        elif "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
    
    def test_client_initialization_with_api_key(self):
        """API 키가 있을 때 클라이언트 초기화"""
        # Given: API 키 설정
        os.environ["ANTHROPIC_API_KEY"] = "test-api-key"
        
        # When: 클라이언트 생성
        client = LiteLLMClient()
        
        # Then: 올바르게 초기화됨
        assert client.claude_api_key == "test-api-key"
        assert client.default_model == "claude-3-5-sonnet-20241022"
    
    def test_client_initialization_without_api_key(self):
        """API 키가 없을 때 클라이언트 초기화"""
        # Given: API 키 제거
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        
        # When: 클라이언트 생성
        client = LiteLLMClient()
        
        # Then: API 키가 None이지만 초기화됨
        assert client.claude_api_key is None
        assert client.default_model == "claude-3-5-sonnet-20241022"
    
    @patch('claude_litellm_proxy.proxy.litellm_client.litellm.acompletion')
    async def test_call_claude_api_success(self, mock_completion):
        """성공적인 Claude API 호출"""
        # Given: 클라이언트와 모의 응답 설정
        os.environ["ANTHROPIC_API_KEY"] = "test-api-key"
        client = LiteLLMClient()
        
        # 모의 LiteLLM 응답
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Hello, I'm Claude!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        
        mock_completion.return_value = mock_response
        
        # When: API 호출
        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100
        }
        
        response = await client.call_claude_api(request_data)
        
        # Then: 올바른 형식으로 응답 반환
        assert response["content"][0]["text"] == "Hello, I'm Claude!"
        assert response["model"] == "claude-3-5-sonnet-20241022"
        assert response["role"] == "assistant"
        assert response["stop_reason"] == "end_turn"
        assert response["usage"]["input_tokens"] == 10
        assert response["usage"]["output_tokens"] == 5
        
        # LiteLLM 호출 확인
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[1]
        assert call_args["model"] == "claude-3-5-sonnet-20241022"
        assert call_args["messages"] == [{"role": "user", "content": "Hello"}]
        assert call_args["max_tokens"] == 100
        assert call_args["api_key"] == "test-api-key"
    
    @patch('claude_litellm_proxy.proxy.litellm_client.litellm.acompletion')
    async def test_call_claude_api_with_default_model(self, mock_completion):
        """기본 모델로 Claude API 호출"""
        # Given: 클라이언트 설정 (모델 미지정)
        os.environ["ANTHROPIC_API_KEY"] = "test-api-key"
        client = LiteLLMClient()
        
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 3
        
        mock_completion.return_value = mock_response
        
        # When: 모델 미지정으로 API 호출
        request_data = {
            "messages": [{"role": "user", "content": "Test"}]
        }
        
        await client.call_claude_api(request_data)
        
        # Then: 기본 모델 사용
        call_args = mock_completion.call_args[1]
        assert call_args["model"] == "claude-3-5-sonnet-20241022"
        assert call_args["max_tokens"] == 4096  # 기본값
        assert call_args["temperature"] == 0.7  # 기본값
    
    def test_map_finish_reason(self):
        """finish_reason 매핑 테스트"""
        # Given: 클라이언트 생성
        client = LiteLLMClient()
        
        # When & Then: 각 finish_reason 매핑 확인
        assert client._map_finish_reason("stop") == "end_turn"
        assert client._map_finish_reason("length") == "max_tokens"
        assert client._map_finish_reason("content_filter") == "stop_sequence"
        assert client._map_finish_reason(None) == "end_turn"
        assert client._map_finish_reason("unknown") == "end_turn"
    
    @patch('claude_litellm_proxy.proxy.litellm_client.litellm.acompletion')
    async def test_health_check_success(self, mock_completion):
        """성공적인 헬스체크"""
        # Given: 정상 동작하는 API 설정
        os.environ["ANTHROPIC_API_KEY"] = "test-api-key"
        client = LiteLLMClient()
        
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Hi"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.usage.prompt_tokens = 2
        mock_response.usage.completion_tokens = 1
        
        mock_completion.return_value = mock_response
        
        # When: 헬스체크 실행
        result = await client.health_check()
        
        # Then: 정상 상태 반환
        assert result["status"] == "healthy"
        assert result["model"] == "claude-3-5-sonnet-20241022"
        assert result["api_key_configured"] is True