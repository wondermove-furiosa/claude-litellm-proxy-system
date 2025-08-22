# Phase 2 검증 문서 - LiteLLM 통합 + 민감정보 처리

## 📋 Phase 2 체크리스트

### ✅ LiteLLM 클라이언트 구현
- [x] Claude API 호환 형식 지원 (요청/응답 변환)
- [x] 비동기 API 호출 처리 (litellm.acompletion)
- [x] 모델 설정 및 파라미터 관리 (기본값, 커스텀 설정)
- [x] 에러 처리 및 재시도 메커니즘
- [x] 헬스체크 및 연결 상태 모니터링

### ✅ 로깅 시스템 구현
- [x] 구조화된 로깅 설정 (레벨, 포맷, 핸들러)
- [x] 모듈별 독립적 로거 관리
- [x] 프로덕션 환경 적합한 로그 출력

### ✅ FastAPI 서버 통합
- [x] 애플리케이션 생명주기 관리 (startup/shutdown)
- [x] 마스킹 시스템 + LiteLLM 클라이언트 통합 초기화
- [x] Claude API 엔드포인트 구현 (/v1/messages)
- [x] 인증 시스템 (Bearer 토큰)
- [x] 헬스체크 엔드포인트 (/health)

### ✅ 요청/응답 마스킹 파이프라인
- [x] 요청 내용 마스킹 (messages 배열 처리)
- [x] LiteLLM을 통한 실제 Claude API 호출
- [x] 응답 내용 복원 (content 배열 처리)
- [x] 매핑 정보 일관성 보장

### ✅ 포괄적 테스트 및 검증
- [x] LiteLLM 클라이언트 단위 테스트 (모의 API 응답)
- [x] 통합 시스템 검증 스크립트 (실제 동작 확인)
- [x] 성능 테스트 (응답 시간, 처리량)
- [x] 에러 처리 및 복구 테스트

---

## 🔍 검증 대상 및 세부 내용

### 1. LiteLLM 클라이언트 핵심 기능 검증 (`litellm_client.py`)

**검증 목적**: Claude API와 완벽히 호환되는 LiteLLM 클라이언트가 올바르게 구현되었는지 확인

**검증 내용**:
- **API 키 관리**: 환경변수를 통한 안전한 인증 정보 관리
  ```python
  self.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
  ```
- **요청 형식 변환**: Claude API 요청을 LiteLLM 형식으로 정확한 변환
  - model, messages, max_tokens, temperature 등 모든 파라미터 지원
  - system 메시지, stop_sequences 등 고급 기능 지원
- **응답 형식 변환**: LiteLLM 응답을 Claude API 형식으로 정확한 역변환
  - content 배열 구조 (`[{"type": "text", "text": "..."}]`)
  - usage 토큰 정보 (`input_tokens`, `output_tokens`)
  - stop_reason 매핑 (`stop` → `end_turn`, `length` → `max_tokens`)
- **에러 처리**: API 호출 실패 시 적절한 예외 처리 및 로깅

**검증 방법**: `test_litellm_client.py::TestLiteLLMClient`
```python
async def test_call_claude_api_success(self, mock_completion):
    # LiteLLM 모의 응답 설정
    mock_response = create_mock_litellm_response()
    mock_completion.return_value = mock_response
    
    # Claude API 형식 요청
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 100
    }
    
    response = await client.call_claude_api(request_data)
    
    # Claude API 형식 응답 검증
    assert response["content"][0]["text"] == "Hello, I'm Claude!"
    assert response["usage"]["input_tokens"] == 10
```

**기대 결과**: Claude API와 100% 호환되는 요청/응답 처리

---

### 2. 로깅 시스템 검증 (`logging.py`)

**검증 목적**: 프로덕션 환경에서 안정적이고 구조화된 로깅이 가능한지 확인

**검증 내용**:
- **로거 설정**: 모듈별 독립적 로거 생성 및 관리
  ```python
  logger = setup_logger(__name__, level="INFO")
  ```
- **출력 형식**: 타임스탬프, 모듈명, 레벨, 메시지 포함한 구조화된 형식
- **레벨 관리**: DEBUG, INFO, WARNING, ERROR 레벨별 적절한 출력
- **핸들러 중복 방지**: 동일 모듈에서 여러 번 호출 시 핸들러 중복 생성 방지
- **상위 로거 전파 방지**: 중복 로그 출력 방지

**검증 방법**: 실제 로그 출력 확인
```python
from claude_litellm_proxy.utils.logging import setup_logger
logger = setup_logger("test_module")
logger.info("테스트 메시지")
# 출력: 2025-08-22 12:44:30,695 - test_module - INFO - 테스트 메시지
```

**기대 결과**: 모든 모듈에서 일관되고 구조화된 로그 출력

---

### 3. FastAPI 서버 통합 검증 (`main.py`)

**검증 목적**: 마스킹 시스템과 LiteLLM이 FastAPI 서버에서 완벽하게 통합되어 동작하는지 확인

**검증 내용**:

#### 3.1 애플리케이션 생명주기 관리
- **초기화 순서**: 마스킹 시스템 → LiteLLM 클라이언트 순서로 초기화
- **환경변수 로딩**: Redis 연결 정보, API 키 등 설정 정보 로딩
- **정리 프로세스**: 애플리케이션 종료 시 리소스 정리 (Redis 연결 해제)

#### 3.2 인증 시스템
- **Bearer 토큰**: HTTP Bearer 인증 스키마 사용
- **API 키 검증**: `LITELLM_MASTER_KEY` 환경변수와 비교 검증
- **401 에러**: 잘못된 인증 정보 시 적절한 에러 응답

#### 3.3 헬스체크 엔드포인트 (`/health`)
- **마스킹 시스템 상태**: 초기화 여부 및 Redis 연결 상태
- **LiteLLM 클라이언트 상태**: API 키 설정 여부 및 연결 테스트
- **전체 시스템 상태**: 모든 구성 요소의 통합 상태 보고

#### 3.4 Claude API 프록시 엔드포인트 (`/v1/messages`)
- **요청 파싱**: JSON 요청 본문 파싱 및 유효성 검사
- **마스킹 파이프라인**: messages 배열 내 content 마스킹
- **LiteLLM 호출**: 마스킹된 요청으로 실제 Claude API 호출
- **복원 파이프라인**: 응답 content 배열 내 텍스트 복원
- **에러 처리**: 각 단계별 에러 시 적절한 HTTP 상태 코드 반환

**검증 방법**: HTTP 요청/응답 테스트
```python
# 헬스체크 확인
response = await client.get("/health")
assert response.status_code == 200
assert response.json()["status"] == "healthy"

# 실제 프록시 요청
response = await client.post("/v1/messages", 
    json=claude_request,
    headers={"Authorization": "Bearer sk-litellm-master-key"})
assert response.status_code == 200
```

**기대 결과**: 모든 엔드포인트가 예상대로 동작하고 적절한 응답 반환

---

### 4. 요청/응답 마스킹 파이프라인 검증

**검증 목적**: HTTP 요청/응답 처리 과정에서 민감정보가 완벽하게 마스킹/복원되는지 확인

**검증 내용**:

#### 4.1 요청 마스킹 (`mask_request_content`)
- **messages 배열 처리**: 사용자 메시지 내 민감정보 탐지 및 마스킹
- **매핑 수집**: 모든 마스킹된 값에 대한 매핑 정보 수집
- **구조 보존**: 요청의 JSON 구조는 유지하면서 content만 마스킹
- **다중 메시지**: 여러 메시지가 있는 대화에서도 정확한 처리

#### 4.2 응답 복원 (`unmask_response_content`)
- **content 배열 처리**: Claude API 응답의 content 배열 내 텍스트 복원
- **매핑 적용**: 요청에서 수집된 매핑 정보로 정확한 복원
- **부분 복원**: 응답에 새로 등장한 마스킹 값은 복원하지 않음 (올바른 동작)

#### 4.3 실제 시나리오 테스트
```python
# 복잡한 AWS 인프라 설명 요청
request_content = """
인프라 분석:
- EC2: i-1234567890abcdef0, i-abcdef1234567890a
- VPC: vpc-12345678
- IAM: AKIA1234567890ABCDEF, AKIA9876543210FEDCBA
- S3: company-data-bucket, backup-logs-bucket
"""

# 마스킹된 요청에서 원본 민감정보 완전 제거 확인
masked_request, mappings = await mask_request_content(request_data)
for sensitive in ["i-1234567890abcdef0", "AKIA1234567890ABCDEF"]:
    assert sensitive not in str(masked_request)

# 복원된 응답에서 원본 정보 정확 복원 확인
unmasked_response = await unmask_response_content(claude_response, mappings)
assert "i-1234567890abcdef0" in str(unmasked_response)
```

**기대 결과**: 민감정보 완전 보호 + 정확한 정보 복원

---

### 5. 통합 시스템 검증 (`test_litellm_integration_verification.py`)

**검증 목적**: 전체 시스템이 실제 환경에서 End-to-End로 올바르게 동작하는지 확인

**검증 내용**:

#### 5.1 실제 환경 통합 테스트
- **Redis 연동**: 실제 Redis 서버와의 연결 및 데이터 영속성
- **마스킹 엔진**: 실제 AWS 리소스 패턴 탐지 및 마스킹
- **LiteLLM 클라이언트**: 모의 Claude API 응답으로 통합 검증
- **세션 일관성**: 동일한 민감정보에 대한 일관된 마스킹 결과

#### 5.2 성능 검증
- **응답 시간**: 100개 AWS 리소스를 0.15초 이내 처리
- **메모리 효율성**: 대용량 텍스트 처리 시 메모리 사용량 안정
- **동시성**: 여러 요청 동시 처리 시에도 성능 유지

#### 5.3 보안 검증
- **민감정보 노출 방지**: 마스킹된 요청/응답에서 원본 정보 완전 제거
- **매핑 보안**: Redis에 저장된 매핑 정보의 안전한 관리
- **로깅 보안**: 로그에 민감정보 노출되지 않음

**검증 방법**: 종합 검증 스크립트 실행
```bash
uv run python test_litellm_integration_verification.py
```

**기대 결과**: 
```
🎉 LiteLLM 통합 완료!
✅ 통합 기능: 성공
⚡ 성능: 만족
```

---

### 6. LiteLLM 클라이언트 단위 테스트 검증 (`test_litellm_client.py`)

**검증 목적**: LiteLLM 클라이언트의 모든 기능이 독립적으로 올바르게 동작하는지 확인

**검증 내용**:

#### 6.1 초기화 테스트
- **API 키 있음**: 환경변수에서 올바른 API 키 로딩
- **API 키 없음**: API 키 없이도 초기화 가능 (헬스체크에서 상태 보고)

#### 6.2 API 호출 테스트 
- **성공 케이스**: 정상적인 LiteLLM 응답 처리
- **기본값 적용**: 모델, max_tokens, temperature 기본값 사용
- **파라미터 전달**: system 메시지, stop_sequences 등 고급 파라미터
- **에러 케이스**: API 호출 실패 시 예외 처리

#### 6.3 응답 변환 테스트
- **finish_reason 매핑**: LiteLLM → Claude API 형식 변환
  - `stop` → `end_turn`
  - `length` → `max_tokens`
  - `content_filter` → `stop_sequence`

#### 6.4 헬스체크 테스트
- **정상 상태**: API 호출 성공 시 healthy 상태
- **타임아웃**: 10초 초과 시 timeout 상태
- **에러 상태**: 연결 실패 시 error 상태

**검증 방법**: 모의 객체를 사용한 단위 테스트
```python
@patch('claude_litellm_proxy.proxy.litellm_client.litellm.acompletion')
async def test_call_claude_api_success(self, mock_completion):
    # 각 기능을 독립적으로 테스트
```

**기대 결과**: 모든 단위 테스트 PASSED (6개 테스트)

---

### 7. 전체 시스템 안정성 검증

**검증 목적**: 프로덕션 환경에서도 안정적으로 동작할 수 있는지 확인

**검증 내용**:

#### 7.1 에러 복구 능력
- **Redis 연결 실패**: Redis 서버 다운 시 적절한 에러 메시지
- **LiteLLM API 실패**: Claude API 호출 실패 시 클라이언트에 적절한 응답
- **인증 실패**: 잘못된 API 키 시 401 에러 반환
- **요청 형식 오류**: 잘못된 JSON 시 422 유효성 검사 에러

#### 7.2 리소스 관리
- **메모리 누수 방지**: 장시간 운영 시에도 메모리 사용량 안정
- **연결 관리**: Redis 연결 풀 적절한 관리
- **정리 프로세스**: 애플리케이션 종료 시 모든 리소스 정리

#### 7.3 모니터링 및 관찰성
- **구조화된 로깅**: 모든 주요 이벤트에 대한 로그 기록
- **성능 메트릭**: 처리 시간, 매핑 생성 수 등 성능 지표
- **상태 보고**: 헬스체크를 통한 시스템 상태 모니터링

**검증 방법**: 장시간 실행 및 스트레스 테스트
```bash
# 여러 동시 요청으로 안정성 테스트
for i in {1..10}; do
  curl -X POST http://localhost:8000/v1/messages \
    -H "Authorization: Bearer sk-litellm-master-key" \
    -H "Content-Type: application/json" \
    -d '{"model": "claude-3-5-sonnet", "messages": [{"role": "user", "content": "Test"}]}' &
done
wait
```

**기대 결과**: 모든 요청이 성공적으로 처리되고 시스템 안정성 유지

---

## 🚀 검증 실행 방법

### 전체 Phase 2 검증 실행
```bash
# 1. 의존성 및 환경 설정
uv sync
export ANTHROPIC_API_KEY="your-api-key"  # 실제 테스트 시

# 2. Redis 서버 시작
docker run -d -p 6379:6379 redis:alpine

# 3. LiteLLM 클라이언트 단위 테스트
uv run pytest tests/test_litellm_client.py -v

# 4. 통합 시스템 검증
uv run python test_litellm_integration_verification.py

# 5. 전체 테스트 실행 (Phase 1 + 2)
uv run pytest tests/ -v --tb=short

# 6. 타입 체크 및 코드 품질
uv run mypy src/claude_litellm_proxy/
uv run black --check src/
```

### FastAPI 서버 실제 실행 테스트
```bash
# 서버 시작
uv run uvicorn claude_litellm_proxy.main:app --reload --port 8000

# 헬스체크 확인
curl http://localhost:8000/health

# 실제 API 요청 테스트
curl -X POST http://localhost:8000/v1/messages \
  -H "Authorization: Bearer sk-litellm-master-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet",
    "messages": [{"role": "user", "content": "Analyze EC2 i-1234567890abcdef0"}],
    "max_tokens": 100
  }'
```

## ✅ 검증 완료 기준

Phase 2가 성공적으로 완료되었다고 판단하는 기준:

1. **LiteLLM 클라이언트 테스트**: 6개 단위 테스트 모두 PASSED
2. **통합 검증 스크립트**: "🎉 LiteLLM 통합 완료!" 메시지 출력
3. **전체 테스트 통과**: Phase 1 + Phase 2 모든 테스트 통과
4. **성능 요구사항**: 100개 리소스 0.2초 이내 처리
5. **실제 서버 동작**: FastAPI 서버가 정상적으로 HTTP 요청 처리
6. **마스킹 파이프라인**: 요청→마스킹→API호출→복원 전 과정 완벽 동작

이 모든 조건이 만족되면 Phase 2의 LiteLLM 통합이 프로덕션 준비 완료 상태입니다.