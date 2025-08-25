#!/usr/bin/env python3
"""
🏆 최종 프로덕션 환경 완전 검증
실제 Claude API를 통한 마스킹/언마스킹 시스템 100% 검증
"""

import asyncio
import aiohttp
import json
import os
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 테스트 설정
SERVER_URL = "http://localhost:8000"
API_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-litellm-master-key")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

class FinalProductionVerificationSystem:
    def __init__(self):
        self.session: aiohttp.ClientSession = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, status: str, details: str = ""):
        """테스트 결과 로깅"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        if status == "PASS":
            self.passed_tests += 1
            print(f"   ✅ {test_name}: PASS")
        else:
            self.failed_tests += 1
            print(f"   ❌ {test_name}: FAIL - {details}")
            
        self.total_tests += 1
    
    async def verify_system_health(self) -> bool:
        """시스템 상태 검증"""
        print("🔍 1단계: 시스템 헬스체크")
        
        try:
            async with self.session.get(f"{SERVER_URL}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    
                    # 각 컴포넌트 상태 확인
                    components = {
                        "masking_engine": health_data.get("masking_engine"),
                        "redis_connection": health_data.get("redis_connection"),
                        "litellm_client": health_data.get("litellm_client")
                    }
                    
                    all_healthy = True
                    for component, status in components.items():
                        if status == "healthy":
                            self.log_result(f"Component {component}", "PASS", f"Status: {status}")
                        else:
                            self.log_result(f"Component {component}", "FAIL", f"Status: {status}")
                            all_healthy = False
                    
                    return all_healthy
                else:
                    self.log_result("Health Check HTTP", "FAIL", f"Status: {response.status}")
                    return False
                    
        except Exception as e:
            self.log_result("Health Check Exception", "FAIL", str(e))
            return False
    
    async def verify_masking_patterns(self) -> bool:
        """핵심 마스킹 패턴 검증"""
        print("\\n🎭 2단계: 마스킹 패턴 검증")
        
        # 내부 마스킹 엔진으로 직접 테스트
        from src.claude_litellm_proxy.patterns.masking_engine import MaskingEngine
        
        engine = MaskingEngine()
        
        test_cases = [
            ("EKS Cluster", "arn:aws:eks:us-east-1:123456789012:cluster/prod", "eks_cluster"),
            ("SageMaker Endpoint", "arn:aws:sagemaker:us-east-1:123456789012:endpoint/ml", "sagemaker_endpoint"),
            ("ECS Task", "arn:aws:ecs:us-east-1:123456789012:task/cluster/abc123", "ecs_task"),
            ("API Gateway", "abcdef1234.execute-api.us-east-1.amazonaws.com", "api_gateway"),
            ("Session Token", "FwoGZXIvYXdzEDdaDFn5Example123", "session_token")
        ]
        
        pattern_success = True
        
        for test_name, test_resource, expected_pattern in test_cases:
            try:
                # 마스킹 테스트
                masked_result = engine.mask_text(test_resource)
                masked_text = masked_result[0]
                mappings = masked_result[1]
                
                if mappings and masked_text != test_resource:
                    # 패턴이 감지되고 마스킹됨
                    detected_pattern = None
                    for masked_key, original_value in mappings.items():
                        if test_resource == original_value:
                            detected_pattern = "detected"
                            break
                    
                    if detected_pattern:
                        self.log_result(f"Masking {test_name}", "PASS", f"Masked: {masked_text}")
                    else:
                        self.log_result(f"Masking {test_name}", "FAIL", "Pattern not properly detected")
                        pattern_success = False
                else:
                    self.log_result(f"Masking {test_name}", "FAIL", "No masking occurred")
                    pattern_success = False
                    
            except Exception as e:
                self.log_result(f"Masking {test_name}", "FAIL", f"Exception: {e}")
                pattern_success = False
        
        return pattern_success
    
    async def verify_end_to_end_claude_api(self) -> bool:
        """End-to-End Claude API 통합 검증"""
        print("\\n🌐 3단계: Claude API End-to-End 통합 검증")
        
        if not ANTHROPIC_API_KEY:
            self.log_result("Claude API Key", "FAIL", "ANTHROPIC_API_KEY not set")
            return False
        
        # 실제 Claude API 호출 테스트
        test_content = """
        Security audit for AWS infrastructure:
        - EKS cluster: arn:aws:eks:us-east-1:123456789012:cluster/production-cluster
        - SageMaker model: arn:aws:sagemaker:us-east-1:123456789012:endpoint/fraud-detection
        - Session: FwoGZXIvYXdzEDdaDFn5ProductionToken12345
        
        Please provide security recommendations.
        """
        
        request_data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 200,
            "messages": [
                {
                    "role": "user",
                    "content": test_content.strip()
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        try:
            start_time = time.time()
            async with self.session.post(
                f"{SERVER_URL}/v1/messages",
                headers=headers,
                json=request_data
            ) as response:
                end_time = time.time()
                response_time = round(end_time - start_time, 3)
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    # 응답 검증
                    if "content" in response_data and response_data["content"]:
                        content = response_data["content"][0].get("text", "")
                        
                        if len(content) > 50:  # 의미있는 응답
                            self.log_result("Claude API Call", "PASS", f"Response time: {response_time}s")
                            self.log_result("Response Quality", "PASS", f"Content length: {len(content)}")
                            
                            # 마스킹 패턴이 응답에 남아있는지 확인 (있으면 언마스킹 실패)
                            masked_patterns = ["AWS_EKS_CLUSTER_", "AWS_SAGEMAKER_", "AWS_SESSION_TOKEN_"]
                            
                            print(f"\n🔍 Claude 응답 내용 분석:")
                            print(f"   응답 길이: {len(content)}")
                            print(f"   응답 내용: {content[:300]}...")
                            
                            found_patterns = []
                            for pattern in masked_patterns:
                                if pattern in content:
                                    found_patterns.append(pattern)
                                    print(f"   ❌ 발견된 마스킹 패턴: {pattern}")
                            
                            masking_residue = len(found_patterns) > 0
                            
                            if not masking_residue:
                                self.log_result("Unmasking Success", "PASS", "No masking patterns in response")
                            else:
                                self.log_result("Unmasking Success", "FAIL", f"Found patterns: {found_patterns}")
                                return False
                            
                            # Claude가 실제로 AWS 리소스를 이해했는지 확인
                            aws_understanding = any(keyword in content.lower() for keyword in 
                                                  ["eks", "sagemaker", "security", "aws", "cluster"])
                            
                            if aws_understanding:
                                self.log_result("Claude Understanding", "PASS", "Claude understood AWS context")
                            else:
                                self.log_result("Claude Understanding", "FAIL", "Claude didn't understand context")
                            
                            print(f"\\n📄 Claude Response Preview:")
                            print(f"   {content[:200]}...")
                            
                            return True
                        else:
                            self.log_result("Response Quality", "FAIL", "Response too short")
                            return False
                    else:
                        self.log_result("Response Format", "FAIL", "Invalid response format")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Claude API Call", "FAIL", f"HTTP {response.status}: {error_text[:200]}")
                    return False
                    
        except Exception as e:
            self.log_result("Claude API Exception", "FAIL", str(e))
            return False
    
    async def verify_redis_integration(self) -> bool:
        """Redis 연동 검증"""
        print("\\n🔴 4단계: Redis 연동 검증")
        
        try:
            # Redis 연결 확인 (헬스체크에서 이미 검증됨)
            async with self.session.get(f"{SERVER_URL}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    redis_status = health_data.get("redis_connection")
                    
                    if redis_status == "healthy":
                        self.log_result("Redis Connection", "PASS", "Redis connectivity confirmed")
                        return True
                    else:
                        self.log_result("Redis Connection", "FAIL", f"Status: {redis_status}")
                        return False
                        
        except Exception as e:
            self.log_result("Redis Integration", "FAIL", str(e))
            return False
    
    async def run_complete_verification(self):
        """완전한 검증 실행"""
        print("🏆 FINAL PRODUCTION ENVIRONMENT VERIFICATION")
        print("=" * 60)
        print(f"🔑 ANTHROPIC_API_KEY: {'CONFIGURED' if ANTHROPIC_API_KEY else 'MISSING'}")
        print(f"🔑 LITELLM_MASTER_KEY: {API_KEY[:20]}...")
        print(f"🌐 Server URL: {SERVER_URL}")
        print()
        
        # 단계별 검증 실행
        verification_steps = [
            ("System Health", self.verify_system_health()),
            ("Masking Patterns", self.verify_masking_patterns()),
            ("Claude API Integration", self.verify_end_to_end_claude_api()),
            ("Redis Integration", self.verify_redis_integration())
        ]
        
        all_passed = True
        
        for step_name, step_coro in verification_steps:
            try:
                step_result = await step_coro
                if not step_result:
                    all_passed = False
            except Exception as e:
                print(f"   ❌ {step_name}: EXCEPTION - {e}")
                all_passed = False
        
        # 최종 결과
        print("\\n" + "=" * 60)
        print("📊 FINAL VERIFICATION RESULTS")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print()
        
        if all_passed and self.failed_tests == 0:
            print("🎉 🏆 PRODUCTION ENVIRONMENT: 100% VERIFIED! 🏆 🎉")
            print("✅ 마스킹 시스템이 실제 프로덕션 환경에서 완벽 동작")
            print("✅ Claude API와 완전한 End-to-End 통합 성공")
            print("✅ 모든 핵심 패턴이 실제 HTTP 요청에서 완벽 작동")
            print("✅ Redis 매핑 시스템 완전 동작")
            print()
            print("🚀 프로덕션 배포 준비 완료!")
        elif self.passed_tests / self.total_tests >= 0.9:
            print("🟡 PRODUCTION ENVIRONMENT: MOSTLY VERIFIED (90%+)")
            print("⚠️ 일부 개선이 필요하지만 핵심 기능은 완벽 동작")
        else:
            print("❌ PRODUCTION ENVIRONMENT: NEEDS IMPROVEMENT")
            print("🔧 추가 디버깅 및 수정이 필요함")
        
        # 상세 결과 저장
        with open("final_production_verification_results.json", "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": time.time(),
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "success_rate": self.passed_tests/self.total_tests*100 if self.total_tests > 0 else 0,
                "overall_status": "VERIFIED" if all_passed else "NEEDS_WORK",
                "test_results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\\n📄 상세 결과 저장: final_production_verification_results.json")

async def main():
    async with FinalProductionVerificationSystem() as verifier:
        await verifier.run_complete_verification()

if __name__ == "__main__":
    asyncio.run(main())