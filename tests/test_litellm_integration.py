"""
LiteLLM 통합 테스트
실제 FastAPI + LiteLLM 서버 테스트

Red-Green-Refactor TDD, Mock 절대 금지
"""

import pytest
import asyncio
import httpx
from typing import Dict, Any

# Red Phase: 아직 구현되지 않은 모듈
try:
    from claude_litellm_proxy.proxy.litellm_server import LiteLLMServer
    from claude_litellm_proxy.main import app  # FastAPI 앱
except ImportError:
    LiteLLMServer = None
    app = None


class TestLiteLLMIntegration:
    """LiteLLM 통합 테스트"""

    @pytest.fixture(autouse=True)
    async def setup_server(self):
        """테스트용 서버 설정"""
        if app is None:
            pytest.skip("LiteLLM 서버가 아직 구현되지 않음 (Red Phase)")
        
        # 실제 FastAPI 테스트 클라이언트
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(base_url=self.base_url)
        
        yield
        
        await self.client.aclose()

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """헬스체크 엔드포인트 테스트"""
        # Red: 아직 구현되지 않아서 실패 예상
        response = await self.client.get("/health")
        
        # Green: 정상 응답해야 함
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "masking_engine" in data
        assert "redis_connection" in data

    @pytest.mark.asyncio  
    async def test_claude_api_proxy_format(self):
        """Claude API 호환 형식 테스트"""
        # 실제 Claude API와 동일한 요청 형식
        claude_request = {
            "model": "claude-3-5-sonnet",
            "messages": [
                {
                    "role": "user", 
                    "content": "Analyze this AWS setup: EC2 i-1234567890abcdef0 in VPC vpc-12345678 with IAM key AKIA1234567890ABCDEF"
                }
            ],
            "max_tokens": 1024
        }
        
        # Red: 프록시 엔드포인트 구현 전 실패 예상
        response = await self.client.post(
            "/v1/messages",
            json=claude_request,
            headers={
                "Authorization": "Bearer sk-litellm-master-key",
                "Content-Type": "application/json"
            }
        )
        
        # Green: 성공 응답해야 함
        assert response.status_code == 200
        
        data = response.json()
        assert "content" in data
        assert isinstance(data["content"], list)
        
        # 응답에서 민감정보가 마스킹되었는지 확인
        response_text = str(data["content"])
        
        # 원본 민감정보가 노출되면 안됨
        assert "i-1234567890abcdef0" not in response_text
        assert "vpc-12345678" not in response_text  
        assert "AKIA1234567890ABCDEF" not in response_text
        
        # 마스킹된 형태가 포함되어야 함
        assert any(masked in response_text for masked in ["ec2-", "vpc-", "iam-"])

    @pytest.mark.asyncio
    async def test_masking_middleware_integration(self):
        """마스킹 미들웨어 통합 테스트"""
        # 민감정보가 포함된 요청
        request_data = {
            "model": "claude-3-5-sonnet",
            "messages": [
                {
                    "role": "user",
                    "content": """
                    Review our infrastructure:
                    - Primary DB: prod-mysql-database  
                    - EC2 Instances: i-1234567890abcdef0, i-abcdef1234567890
                    - S3 Buckets: company-logs-bucket, backup-data-bucket
                    - Security Group: sg-87654321
                    - IAM Keys: AKIA1234567890ABCDEF, AKIA9876543210FEDCBA
                    """
                }
            ],
            "max_tokens": 500
        }
        
        # Red: 미들웨어 구현 전 실패 예상
        response = await self.client.post(
            "/v1/messages",
            json=request_data,
            headers={"Authorization": "Bearer sk-litellm-master-key"}
        )
        
        # Green: 요청 처리 성공
        assert response.status_code == 200
        
        # 응답에서 모든 민감정보가 마스킹되었는지 확인
        response_content = response.text
        
        sensitive_data = [
            "i-1234567890abcdef0",
            "i-abcdef1234567890", 
            "company-logs-bucket",
            "backup-data-bucket",
            "sg-87654321",
            "AKIA1234567890ABCDEF",
            "AKIA9876543210FEDCBA"
        ]
        
        for sensitive in sensitive_data:
            assert sensitive not in response_content, f"민감정보 노출: {sensitive}"

    @pytest.mark.asyncio
    async def test_streaming_response_masking(self):
        """스트리밍 응답 마스킹 테스트"""
        request_data = {
            "model": "claude-3-5-sonnet",
            "messages": [
                {
                    "role": "user",
                    "content": "Explain the security of EC2 instance i-1234567890abcdef0"
                }
            ],
            "max_tokens": 200,
            "stream": True  # 스트리밍 요청
        }
        
        # Red: 스트리밍 마스킹 구현 전 실패 예상
        async with self.client.stream(
            "POST",
            "/v1/messages", 
            json=request_data,
            headers={"Authorization": "Bearer sk-litellm-master-key"}
        ) as response:
            
            assert response.status_code == 200
            
            # 스트리밍 데이터에서도 마스킹되어야 함
            async for chunk in response.aiter_text():
                # 민감정보가 노출되면 안됨
                assert "i-1234567890abcdef0" not in chunk

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """오류 처리 테스트"""
        # 잘못된 요청 형식
        invalid_request = {
            "model": "invalid-model",
            "messages": "invalid format"  # 잘못된 형식
        }
        
        # Red: 오류 처리 구현 전 실패 예상  
        response = await self.client.post(
            "/v1/messages",
            json=invalid_request,
            headers={"Authorization": "Bearer sk-litellm-master-key"}
        )
        
        # Green: 적절한 오류 응답
        assert response.status_code in [400, 422]  # Bad Request or Validation Error
        
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

    @pytest.mark.asyncio
    async def test_unauthorized_access(self):
        """인증 실패 테스트"""
        request_data = {
            "model": "claude-3-5-sonnet", 
            "messages": [{"role": "user", "content": "test"}]
        }
        
        # 잘못된 API 키로 요청
        response = await self.client.post(
            "/v1/messages",
            json=request_data,
            headers={"Authorization": "Bearer invalid-key"}
        )
        
        # Red: 인증 구현 전 실패 예상
        assert response.status_code == 401  # Unauthorized

    @pytest.mark.asyncio
    async def test_response_time_performance(self):
        """응답 시간 성능 테스트"""
        import time
        
        request_data = {
            "model": "claude-3-5-sonnet",
            "messages": [
                {
                    "role": "user",
                    "content": "Quick analysis of EC2 i-1234567890abcdef0"
                }
            ],
            "max_tokens": 100
        }
        
        start_time = time.time()
        
        # Red: 성능 최적화 전 실패 가능
        response = await self.client.post(
            "/v1/messages",
            json=request_data,
            headers={"Authorization": "Bearer sk-litellm-master-key"}
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Green: 5초 이내 응답 (성능 요구사항)
        assert response.status_code == 200
        assert duration < 5.0, f"응답 시간 초과: {duration:.2f}초"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """동시 요청 처리 테스트"""
        async def make_request(i):
            request_data = {
                "model": "claude-3-5-sonnet",
                "messages": [
                    {
                        "role": "user", 
                        "content": f"Test {i}: EC2 i-{i:016x}a with IAM AKIA{i:016d}"
                    }
                ],
                "max_tokens": 50
            }
            
            response = await self.client.post(
                "/v1/messages",
                json=request_data,
                headers={"Authorization": "Bearer sk-litellm-master-key"}
            )
            return response.status_code
        
        # 10개 동시 요청
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Red: 동시성 처리 구현 전 실패 가능
        # Green: 모든 요청 성공
        assert all(status == 200 for status in results)


if __name__ == "__main__":
    print("🚨 TDD Red Phase: LiteLLM 통합 테스트")
    print("실제 FastAPI 서버 및 LiteLLM 필요")
    pytest.main([__file__, "-v"])