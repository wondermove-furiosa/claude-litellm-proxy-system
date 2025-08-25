"""
FastAPI + LiteLLM 통합 서버

Claude Code SDK와 호환되는 HTTP 프록시 서버
민감정보 마스킹 미들웨어 통합
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import os
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 통합 마스킹 시스템
from .proxy.integrated_masking import IntegratedMaskingSystem
from .proxy.litellm_client import LiteLLMClient
from .sdk.claude_code_client import ClaudeCodeHeadlessClient
from .utils.logging import setup_logger

# 로거 설정
logger = setup_logger(__name__)

# 전역 시스템들
masking_system: Optional[IntegratedMaskingSystem] = None
litellm_client: Optional[LiteLLMClient] = None
claude_code_client: Optional[ClaudeCodeHeadlessClient] = None

# 보안 스키마
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global masking_system, litellm_client, claude_code_client
    
    # 시작 시 초기화
    logger.info("🚀 Claude Code SDK + LiteLLM 프록시 서버 시작")
    
    # Redis 연결 설정
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    
    # 마스킹 시스템 초기화
    masking_system = IntegratedMaskingSystem(
        redis_host=redis_host,
        redis_port=redis_port,
        redis_db=redis_db
    )
    logger.info("✅ 마스킹 시스템 초기화 완료")
    
    # LiteLLM 클라이언트 초기화
    litellm_client = LiteLLMClient()
    logger.info("✅ LiteLLM 클라이언트 초기화 완료")
    
    # Claude Code SDK 클라이언트 초기화 (Phase 3)
    proxy_url = os.getenv("LITELLM_PROXY_URL", "http://localhost:8000")
    auth_token = os.getenv("LITELLM_MASTER_KEY", "sk-litellm-master-key")
    claude_code_client = ClaudeCodeHeadlessClient(
        proxy_url=proxy_url,
        auth_token=auth_token
    )
    logger.info("✅ Claude Code SDK 클라이언트 초기화 완료")
    
    yield
    
    # 종료 시 정리
    if masking_system:
        await masking_system.close()
        logger.info("🔄 마스킹 시스템 종료 완료")


# FastAPI 앱 생성
app = FastAPI(
    title="Claude LiteLLM Proxy",
    description="Claude Code SDK + LiteLLM 통합 프록시 (민감정보 마스킹)",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """API 키 검증"""
    expected_key = os.getenv("LITELLM_MASTER_KEY", "sk-litellm-master-key")
    
    if credentials.credentials != expected_key:
        logger.warning(f"인증 실패: {credentials.credentials[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return credentials.credentials


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """헬스체크 엔드포인트"""
    global masking_system, litellm_client, claude_code_client
    
    try:
        # 마스킹 시스템 상태 확인
        masking_status = "healthy" if masking_system else "not_initialized"
        
        # Redis 연결 확인
        redis_status = "unknown"
        if masking_system:
            try:
                # 간단한 매핑 테스트
                test_masked, test_mapping = await masking_system.mask_text("test")
                redis_status = "healthy" if test_mapping or test_masked == "test" else "error"
            except Exception as e:
                logger.error(f"Redis 상태 확인 실패: {e}")
                redis_status = "error"
        
        # LiteLLM 클라이언트 상태 확인
        litellm_status = "not_initialized"
        if litellm_client:
            litellm_health = await litellm_client.health_check()
            litellm_status = litellm_health["status"]
        
        # Claude Code SDK 클라이언트 상태 확인 (Phase 3)
        claude_code_status = "not_initialized"
        if claude_code_client:
            try:
                claude_health = await claude_code_client.health_check()
                claude_code_status = claude_health["status"]
            except Exception as e:
                logger.error(f"Claude Code SDK 상태 확인 실패: {e}")
                claude_code_status = "error"
        
        return {
            "status": "healthy",
            "masking_engine": masking_status,
            "redis_connection": redis_status,
            "litellm_client": litellm_status,
            "claude_code_sdk": claude_code_status,
            "version": "0.1.0"
        }
    
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@app.post("/v1/messages")
async def claude_messages_proxy(
    request: Request,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Claude API /v1/messages 엔드포인트 프록시
    민감정보 마스킹 적용
    """
    global masking_system, litellm_client
    
    if not masking_system:
        raise HTTPException(
            status_code=503,
            detail="Masking system not initialized"
        )
    
    if not litellm_client:
        raise HTTPException(
            status_code=503,
            detail="LiteLLM client not initialized"
        )
    
    try:
        # 요청 본문 파싱
        request_data = await request.json()
        
        logger.info(f"Claude API 요청 수신: model={request_data.get('model', 'unknown')}")
        
        # 요청에서 민감정보 마스킹
        masked_request, request_mappings = await mask_request_content(request_data)
        
        # 실제 LiteLLM을 통한 Claude API 호출
        claude_response = await litellm_client.call_claude_api(masked_request)
        
        # 응답에서 민감정보 복원
        unmasked_response = await unmask_response_content(claude_response, request_mappings)
        
        logger.info("Claude API 응답 처리 완료")
        return unmasked_response
    
    except Exception as e:
        logger.error(f"Claude API 프록시 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Proxy error: {str(e)}"
        )


async def mask_request_content(request_data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, str]]:
    """요청 내용에서 민감정보 마스킹"""
    global masking_system
    
    all_mappings = {}
    masked_request = request_data.copy()
    
    # messages 배열 처리
    if "messages" in request_data and isinstance(request_data["messages"], list):
        masked_messages = []
        
        for message in request_data["messages"]:
            if isinstance(message, dict) and "content" in message:
                # 내용 마스킹
                masked_content, mappings = await masking_system.mask_text(message["content"])
                all_mappings.update(mappings)
                
                # 마스킹된 메시지 생성
                masked_message = message.copy()
                masked_message["content"] = masked_content
                masked_messages.append(masked_message)
            else:
                masked_messages.append(message)
        
        masked_request["messages"] = masked_messages
    
    return masked_request, all_mappings


async def unmask_response_content(response_data: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
    """응답 내용에서 민감정보 복원"""
    global masking_system
    
    if not mappings:
        return response_data
    
    unmasked_response = response_data.copy()
    
    # content 배열 처리 (Claude API 응답 형식)
    if "content" in response_data and isinstance(response_data["content"], list):
        unmasked_content = []
        
        for content_item in response_data["content"]:
            if isinstance(content_item, dict) and "text" in content_item:
                # 텍스트 내용 복원
                unmasked_text = await masking_system.unmask_text(content_item["text"])
                
                unmasked_item = content_item.copy()
                unmasked_item["text"] = unmasked_text
                unmasked_content.append(unmasked_item)
            else:
                unmasked_content.append(content_item)
        
        unmasked_response["content"] = unmasked_content
    
    return unmasked_response




@app.post("/v1/claude-code")
async def claude_code_headless_proxy(
    request: Request,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Claude Code SDK headless 모드 프록시 엔드포인트 (Phase 3-2: 마스킹 통합)
    
    완전한 플로우:
    Claude Code SDK (-p headless) 
    → 이 엔드포인트 
    → 요청 마스킹 (Redis)
    → LiteLLM → Claude API 
    → 응답 언마스킹 (Redis)
    → Claude Code SDK
    """
    global claude_code_client, masking_system
    
    if not claude_code_client:
        raise HTTPException(
            status_code=503,
            detail="Claude Code SDK client not initialized"
        )
    
    if not masking_system:
        raise HTTPException(
            status_code=503,
            detail="Masking system not initialized"
        )
    
    try:
        # 요청 본문 파싱
        request_data = await request.json()
        
        prompt = request_data.get("prompt", "")
        if not prompt:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: prompt"
            )
        
        logger.info(f"Claude Code SDK 요청 수신: {prompt[:100]}...")
        
        # Phase 3-2: 요청 프롬프트에서 민감정보 마스킹
        logger.info("🎭 요청 마스킹 시작...")
        masked_prompt, prompt_mappings = await masking_system.mask_text(prompt)
        
        if prompt_mappings:
            logger.info(f"🔒 민감정보 {len(prompt_mappings)}개 마스킹됨")
        
        # 마스킹된 프롬프트로 Claude Code SDK 실행
        # 이는 자동으로 ANTHROPIC_BASE_URL (우리 /v1/messages 프록시)로 리다이렉트됨
        masked_request_data = request_data.copy()
        masked_request_data["prompt"] = masked_prompt
        
        result = await claude_code_client.query_headless(
            prompt=masked_prompt,
            allowed_tools=request_data.get("allowed_tools", ["Read", "Write", "Bash"]),
            system_prompt=request_data.get("system_prompt"),
            working_directory=request_data.get("working_directory")
        )
        
        # Phase 3-2: 응답에서 민감정보 복원
        logger.info("🔓 응답 언마스킹 시작...")
        if result and "content" in result and result["content"]:
            for content_item in result["content"]:
                if "text" in content_item:
                    # 응답 텍스트 언마스킹
                    content_item["text"] = await masking_system.unmask_text(content_item["text"])
        
        logger.info("Claude Code SDK 응답 처리 완료 (마스킹/언마스킹 포함)")
        return result
    
    except Exception as e:
        logger.error(f"Claude Code SDK 프록시 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Claude Code SDK proxy error: {str(e)}"
        )


@app.post("/v1/claude-code/analyze")
async def claude_code_analyze_proxy(
    request: Request,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Claude Code SDK 코드 분석 전용 엔드포인트 (Phase 3-2: 마스킹 통합)
    
    AWS 리소스가 포함된 코드 분석 시 자동으로 민감정보 마스킹/언마스킹 처리
    """
    global claude_code_client, masking_system
    
    if not claude_code_client:
        raise HTTPException(
            status_code=503,
            detail="Claude Code SDK client not initialized"
        )
    
    if not masking_system:
        raise HTTPException(
            status_code=503,
            detail="Masking system not initialized"
        )
    
    try:
        # 요청 본문 파싱
        request_data = await request.json()
        
        code_path = request_data.get("code_path", "")
        analysis_type = request_data.get("analysis_type", "security")
        specific_prompt = request_data.get("specific_prompt")
        
        if not code_path:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: code_path"
            )
        
        logger.info(f"Claude Code SDK 코드 분석 요청: {code_path}")
        
        # Phase 3-2: specific_prompt가 있으면 마스킹 처리
        if specific_prompt:
            logger.info("🎭 분석 프롬프트 마스킹 시작...")
            masked_prompt, prompt_mappings = await masking_system.mask_text(specific_prompt)
            
            if prompt_mappings:
                logger.info(f"🔒 분석 프롬프트에서 민감정보 {len(prompt_mappings)}개 마스킹됨")
            
            specific_prompt = masked_prompt
        
        # 코드 분석 실행 (마스킹된 프롬프트 사용)
        result = await claude_code_client.analyze_code(
            code_path=code_path,
            analysis_type=analysis_type,
            specific_prompt=specific_prompt
        )
        
        # Phase 3-2: 분석 결과에서 민감정보 복원
        logger.info("🔓 분석 결과 언마스킹 시작...")
        if result and "content" in result and result["content"]:
            for content_item in result["content"]:
                if "text" in content_item:
                    # 분석 결과 텍스트 언마스킹
                    content_item["text"] = await masking_system.unmask_text(content_item["text"])
        
        logger.info("Claude Code SDK 코드 분석 완료 (마스킹/언마스킹 포함)")
        return result
    
    except Exception as e:
        logger.error(f"Claude Code SDK 코드 분석 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Claude Code SDK analyze error: {str(e)}"
        )


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Claude Code SDK + LiteLLM Proxy Server",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "claude_api": "/v1/messages",
            "claude_code_headless": "/v1/claude-code",
            "claude_code_analyze": "/v1/claude-code/analyze"
        }
    }