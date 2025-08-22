"""
Claude Code SDK Headless 클라이언트

Phase 3 핵심 구현: Claude Code SDK → HTTP Proxy → LiteLLM 플로우
- 모든 호출은 headless 모드 (-p 플래그)로만 실행
- 대화형/세션 없음 (stateless)
- 우리 프록시 서버로 리다이렉트
"""

import os
import asyncio
import subprocess
import json
from typing import Dict, Any, Optional, List
from ..utils.logging import setup_logger

# 로거 설정
logger = setup_logger(__name__)


class ClaudeCodeHeadlessClient:
    """
    Claude Code SDK Headless 전용 클라이언트
    
    핵심 원칙:
    1. 모든 호출은 -p (headless) 플래그 사용
    2. 대화형 모드 절대 사용 금지
    3. ANTHROPIC_BASE_URL로 우리 프록시 리다이렉트
    4. 완전한 stateless 실행
    """
    
    def __init__(
        self,
        proxy_url: str = "http://localhost:8000",
        auth_token: str = "sk-litellm-master-key"
    ):
        """
        Claude Code SDK 클라이언트 초기화
        
        Args:
            proxy_url: 우리 프록시 서버 URL
            auth_token: 인증 토큰 (LITELLM_MASTER_KEY)
        """
        self.proxy_url = proxy_url
        self.auth_token = auth_token
        
        # Claude Code SDK 환경변수 설정
        self._setup_environment()
        
        logger.info(f"Claude Code SDK 클라이언트 초기화 완료 (proxy: {proxy_url})")
    
    def _setup_environment(self) -> None:
        """
        Claude Code SDK 환경변수 설정
        
        핵심: ANTHROPIC_BASE_URL로 우리 프록시 리다이렉트
        """
        # 필수: 우리 프록시로 리다이렉트
        os.environ["ANTHROPIC_BASE_URL"] = self.proxy_url
        os.environ["ANTHROPIC_AUTH_TOKEN"] = self.auth_token
        
        # Telemetry 비활성화 (보안)
        os.environ["DISABLE_TELEMETRY"] = "true"
        os.environ["DISABLE_ERROR_REPORTING"] = "true"
        
        # 디버그 모드 (개발용)
        if os.getenv("ENABLE_DEBUG_LOGGING", "false").lower() == "true":
            os.environ["ANTHROPIC_LOG"] = "debug"
        
        logger.info(f"환경변수 설정 완료: ANTHROPIC_BASE_URL={self.proxy_url}")
    
    async def query_headless(
        self,
        prompt: str,
        allowed_tools: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        working_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Claude Code SDK headless 모드 쿼리 실행
        
        Args:
            prompt: 사용자 프롬프트
            allowed_tools: 허용된 도구 목록 (예: ["Read", "Write", "Bash"])
            max_tokens: 최대 토큰 수
            system_prompt: 시스템 프롬프트
            working_directory: 작업 디렉터리
            
        Returns:
            Claude API 응답 (우리 프록시를 통해 마스킹/언마스킹 처리됨)
            
        중요: 이 함수는 완전한 headless 모드로만 실행됨
        """
        if not prompt.strip():
            raise ValueError("프롬프트가 비어있습니다")
        
        logger.info(f"Claude Code SDK headless 쿼리 시작: {prompt[:100]}...")
        
        try:
            # Claude Code SDK headless 명령 구성
            cmd = self._build_headless_command(
                prompt=prompt,
                allowed_tools=allowed_tools,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                working_directory=working_directory
            )
            
            # headless 모드로 실행
            result = await self._execute_headless_command(cmd, working_directory)
            
            logger.info("Claude Code SDK headless 쿼리 완료")
            return result
            
        except Exception as e:
            logger.error(f"Claude Code SDK headless 쿼리 실패: {e}")
            raise
    
    def _build_headless_command(
        self,
        prompt: str,
        allowed_tools: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        working_directory: Optional[str] = None
    ) -> List[str]:
        """
        Claude Code SDK headless 명령 구성
        
        핵심: -p 플래그로 headless 모드 강제
        """
        cmd = [
            "claude",
            "-p", prompt,  # 핵심: headless 모드 플래그
            "--output-format", "stream-json"  # JSON 출력으로 파싱 용이
        ]
        
        # 허용된 도구 설정
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])
        
        # 시스템 프롬프트 설정
        if system_prompt:
            cmd.extend(["--append-system-prompt", system_prompt])
        
        # 작업 디렉터리 설정
        if working_directory:
            cmd.extend(["--cwd", working_directory])
        
        # 추가 보안 설정
        cmd.extend([
            "--permission-mode", "acceptEdits",  # 파일 편집 권한
            "--verbose"  # 디버깅용 상세 출력
        ])
        
        logger.debug(f"Claude Code SDK 명령: {' '.join(cmd)}")
        return cmd
    
    async def _execute_headless_command(
        self,
        cmd: List[str],
        working_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Claude Code SDK headless 명령 실행
        
        완전한 비동기 실행으로 세션/대화형 모드 방지
        """
        try:
            # 환경변수 준비
            env = os.environ.copy()
            
            # 작업 디렉터리 설정
            cwd = working_directory or os.getcwd()
            
            logger.debug(f"명령 실행: {' '.join(cmd)} (cwd: {cwd})")
            
            # 비동기 subprocess 실행
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd
            )
            
            # 결과 대기 (타임아웃 설정)
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=int(os.getenv("API_TIMEOUT_MS", "30000")) / 1000
                )
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError("Claude Code SDK 실행 타임아웃")
            
            # 결과 처리
            return await self._process_command_result(
                process.returncode, stdout, stderr
            )
            
        except Exception as e:
            logger.error(f"Claude Code SDK 명령 실행 실패: {e}")
            raise
    
    async def _process_command_result(
        self,
        return_code: int,
        stdout: bytes,
        stderr: bytes
    ) -> Dict[str, Any]:
        """
        Claude Code SDK 실행 결과 처리
        """
        stdout_text = stdout.decode('utf-8') if stdout else ""
        stderr_text = stderr.decode('utf-8') if stderr else ""
        
        logger.debug(f"Return code: {return_code}")
        logger.debug(f"Stdout: {stdout_text[:500]}...")
        
        if stderr_text:
            logger.debug(f"Stderr: {stderr_text[:500]}...")
        
        if return_code != 0:
            error_msg = f"Claude Code SDK 실행 실패 (code: {return_code})"
            if stderr_text:
                error_msg += f": {stderr_text}"
            raise RuntimeError(error_msg)
        
        # JSON 응답 파싱 시도
        try:
            # stream-json 형식일 수 있으므로 각 라인을 JSON으로 파싱
            lines = [line.strip() for line in stdout_text.split('\n') if line.strip()]
            
            if not lines:
                return {"content": [{"type": "text", "text": ""}]}
            
            # 마지막 JSON 라인이 최종 응답
            for line in reversed(lines):
                try:
                    result = json.loads(line)
                    if isinstance(result, dict) and "content" in result:
                        return result
                except json.JSONDecodeError:
                    continue
            
            # JSON 파싱 실패시 텍스트 그대로 반환
            return {
                "content": [{"type": "text", "text": stdout_text}],
                "role": "assistant",
                "model": "claude-3-5-sonnet-20241022"
            }
            
        except Exception as e:
            logger.warning(f"JSON 파싱 실패, 텍스트 반환: {e}")
            return {
                "content": [{"type": "text", "text": stdout_text}],
                "role": "assistant",
                "model": "claude-3-5-sonnet-20241022"
            }
    
    async def analyze_code(
        self,
        code_path: str,
        analysis_type: str = "security",
        specific_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        코드 분석 (AWS 리소스 포함)
        
        이 메서드는 민감정보가 포함된 코드를 분석할 때 사용
        우리 프록시를 통해 자동으로 마스킹/언마스킹 처리됨
        """
        if specific_prompt:
            prompt = specific_prompt
        else:
            prompt = f"Analyze the code at {code_path} for {analysis_type} issues. "
            prompt += "Focus on AWS resource configurations and potential security vulnerabilities."
        
        return await self.query_headless(
            prompt=prompt,
            allowed_tools=["Read", "Write", "Bash"],
            working_directory=os.path.dirname(os.path.abspath(code_path))
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Claude Code SDK 연결 상태 확인
        """
        try:
            result = await self.query_headless(
                prompt="Health check - respond with 'OK'",
                allowed_tools=[]
            )
            
            return {
                "status": "healthy",
                "proxy_url": self.proxy_url,
                "claude_code_sdk": "available",
                "response": result
            }
            
        except Exception as e:
            logger.error(f"Claude Code SDK 헬스체크 실패: {e}")
            return {
                "status": "unhealthy",
                "proxy_url": self.proxy_url,
                "claude_code_sdk": "error",
                "error": str(e)
            }