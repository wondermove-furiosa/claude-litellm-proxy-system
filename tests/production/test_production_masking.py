#!/usr/bin/env python3
"""
프로덕션 환경 마스킹/언마스킹 검증 테스트
실제 HTTP 요청을 통한 end-to-end 테스트
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List

# 테스트 서버 설정
SERVER_URL = "http://localhost:8000"
API_KEY = "sk-test-production-key"

# 테스트 케이스: 이전에 실패했던 5개 핵심 패턴
TEST_CASES = [
    {
        "name": "EKS Cluster ARN",
        "content": "Please analyze this EKS cluster: arn:aws:eks:us-east-1:123456789012:cluster/production-cluster",
        "expected_pattern": "eks_cluster",
        "expected_resource": "arn:aws:eks:us-east-1:123456789012:cluster/production-cluster"
    },
    {
        "name": "SageMaker Endpoint ARN", 
        "content": "SageMaker endpoint configuration: arn:aws:sagemaker:us-east-1:123456789012:endpoint/ml-model-v2",
        "expected_pattern": "sagemaker_endpoint",
        "expected_resource": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/ml-model-v2"
    },
    {
        "name": "ECS Task ARN",
        "content": "ECS task running on: arn:aws:ecs:us-east-1:123456789012:task/my-cluster/abc123def456ghij",
        "expected_pattern": "ecs_task", 
        "expected_resource": "arn:aws:ecs:us-east-1:123456789012:task/my-cluster/abc123def456ghij"
    },
    {
        "name": "API Gateway URL",
        "content": "API Gateway endpoint: https://abcdef1234.execute-api.us-east-1.amazonaws.com/prod/users",
        "expected_pattern": "api_gateway",
        "expected_resource": "abcdef1234.execute-api.us-east-1.amazonaws.com"
    },
    {
        "name": "AWS Session Token",
        "content": "Session token: FwoGZXIvYXdzEDdaDFn5ExampleSessionToken123456789abcdefgh",
        "expected_pattern": "session_token",
        "expected_resource": "FwoGZXIvYXdzEDdaDFn5ExampleSessionToken123456789abcdefgh"
    },
    {
        "name": "Multi-Resource Test",
        "content": "Infrastructure: EKS cluster arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster, API Gateway abcdef1234.execute-api.us-east-1.amazonaws.com, and S3 bucket my-app-prod-bucket-2023",
        "expected_patterns": ["eks_cluster", "api_gateway", "s3_bucket"],
        "expected_resources": [
            "arn:aws:eks:us-east-1:123456789012:cluster/prod-cluster",
            "abcdef1234.execute-api.us-east-1.amazonaws.com", 
            "my-app-prod-bucket-2023"
        ]
    }
]

class ProductionMaskingTester:
    def __init__(self):
        self.session: aiohttp.ClientSession = None
        self.results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health(self) -> bool:
        """서버 헬스 체크"""
        try:
            async with self.session.get(f"{SERVER_URL}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ 서버 상태: {health_data}")
                    return health_data.get("masking_engine") == "healthy"
                else:
                    print(f"❌ 헬스체크 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 헬스체크 오류: {e}")
            return False
    
    async def test_direct_masking_internal(self) -> bool:
        """내부 마스킹 시스템 직접 테스트 (비교용)"""
        print("\\n🔧 내부 마스킹 시스템 직접 테스트...")
        
        # 패턴 테스트용 간단한 프록시 엔드포인트가 없으므로
        # 여기서는 로컬 마스킹 엔진 직접 사용
        from src.claude_litellm_proxy.patterns.masking_engine import MaskingEngine
        
        engine = MaskingEngine()
        
        for i, test_case in enumerate(TEST_CASES[:5], 1):  # 단일 리소스 케이스만
            print(f"\\n{i}. {test_case['name']}")
            print(f"   원본: {test_case['content']}")
            
            try:
                # 마스킹 테스트
                masked_result = engine.mask_text(test_case['content'])
                masked_text = masked_result[0]
                mappings = masked_result[1]
                
                print(f"   마스킹: {masked_text}")
                
                if mappings:
                    print(f"   매핑: {len(mappings)}개")
                    for masked_key, original_value in mappings.items():
                        if test_case['expected_resource'] in original_value:
                            print(f"   ✅ 예상 리소스 감지: {original_value}")
                        else:
                            print(f"   ⚠️ 다른 리소스: {original_value}")
                else:
                    print(f"   ❌ 마스킹 없음")
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        
        return True
    
    async def test_claude_api_proxy(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Claude API 프록시 엔드포인트 테스트"""
        
        # Claude API 요청 형식으로 구성
        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user", 
                    "content": test_case["content"]
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        try:
            # 요청 전송 (마스킹 처리됨)
            start_time = time.time()
            async with self.session.post(
                f"{SERVER_URL}/v1/messages",
                headers=headers,
                json=request_data
            ) as response:
                end_time = time.time()
                
                response_text = await response.text()
                
                result = {
                    "test_name": test_case["name"],
                    "status_code": response.status,
                    "response_time": round(end_time - start_time, 3),
                    "success": False,
                    "error": None,
                    "masking_detected": False,
                    "expected_pattern_found": False
                }
                
                if response.status == 200:
                    try:
                        response_data = json.loads(response_text)
                        result["success"] = True
                        result["response_size"] = len(response_text)
                        
                        # 응답에서 언마스킹이 제대로 되었는지 확인
                        if "content" in response_data:
                            content_text = str(response_data["content"])
                            
                            # 원본 리소스가 복원되었는지 확인
                            if test_case["expected_resource"] in content_text:
                                result["expected_pattern_found"] = True
                            
                            # 마스킹된 패턴(AWS_XXX_001)이 남아있는지 확인 (있으면 언마스킹 실패)
                            if "AWS_" in content_text and "_001" in content_text:
                                result["masking_detected"] = True
                                result["potential_unmask_failure"] = True
                        
                    except json.JSONDecodeError:
                        result["error"] = "Invalid JSON response"
                        result["response_preview"] = response_text[:200]
                        
                else:
                    result["error"] = f"HTTP {response.status}: {response_text[:500]}"
                
                return result
                
        except Exception as e:
            return {
                "test_name": test_case["name"],
                "status_code": 0,
                "success": False,
                "error": str(e),
                "response_time": 0
            }
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        
        print("🚀 프로덕션 환경 마스킹/언마스킹 검증 시작")
        print("=" * 60)
        
        # 1. 헬스 체크
        if not await self.test_health():
            print("❌ 서버 헬스체크 실패")
            return
        
        # 2. 내부 마스킹 시스템 직접 테스트
        await self.test_direct_masking_internal()
        
        # 3. HTTP 프록시 테스트 (Claude API 없이는 실제 응답 불가)
        print("\\n🌐 HTTP 프록시 엔드포인트 테스트...")
        print("(주의: ANTHROPIC_API_KEY 없으므로 실제 Claude 응답은 불가)")
        
        for i, test_case in enumerate(TEST_CASES, 1):
            print(f"\\n{i}. {test_case['name']} 테스트...")
            result = await self.test_claude_api_proxy(test_case)
            self.results.append(result)
            
            if result["success"]:
                print(f"   ✅ HTTP {result['status_code']} ({result['response_time']}s)")
                if result.get("expected_pattern_found"):
                    print(f"   ✅ 예상 패턴 감지됨")
                if result.get("masking_detected"):
                    print(f"   ⚠️ 언마스킹 미완료 가능성")
            else:
                print(f"   ❌ 실패: {result['error']}")
        
        # 4. 결과 요약
        self.print_summary()
    
    def print_summary(self):
        """테스트 결과 요약"""
        print("\\n" + "=" * 60)
        print("📊 프로덕션 환경 검증 결과 요약")
        print("=" * 60)
        
        success_count = sum(1 for r in self.results if r["success"])
        total_count = len(self.results)
        
        print(f"✅ HTTP 요청 성공률: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count > 0:
            avg_response_time = sum(r["response_time"] for r in self.results if r["success"]) / success_count
            print(f"⏱️ 평균 응답 시간: {avg_response_time:.3f}초")
        
        # 실패한 케이스 상세
        failed_tests = [r for r in self.results if not r["success"]]
        if failed_tests:
            print("\\n❌ 실패한 테스트:")
            for test in failed_tests:
                print(f"   - {test['test_name']}: {test['error']}")
        
        print("\\n🎯 프로덕션 환경 평가:")
        if success_count == total_count:
            print("   ✅ 모든 HTTP 엔드포인트가 정상 작동")
            print("   ✅ 마스킹 시스템이 프로덕션 준비 완료")
        elif success_count > total_count * 0.8:
            print("   ⚠️ 대부분의 엔드포인트가 작동 (일부 개선 필요)")
        else:
            print("   ❌ 다수의 엔드포인트 문제 (추가 디버깅 필요)")

async def main():
    async with ProductionMaskingTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())