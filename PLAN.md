# Claude Code SDK + LiteLLM 통합 프록시 시스템 구축 계획서

## 📋 프로젝트 개요

### 목표
Claude Code SDK와 LiteLLM을 통합한 HTTP 프록시 시스템을 구축하여, Claude Code의 모든 API 호출을 LiteLLM 게이트웨이를 통해 라우팅하는 시스템을 개발합니다.

### 비즈니스 가치
- **아키텍처 단순화**: 복잡한 멀티 프록시 구조를 단일 게이트웨이로 통합
- **확장성 확보**: LiteLLM을 통해 100+ LLM 제공업체 지원
- **유지보수성 향상**: Python 기반 단일 스택으로 통합
- **개발 효율성**: Claude Code SDK의 헤드리스 모드를 활용한 자동화 가능

### 핵심 기능
1. **HTTP 프록시 게이트웨이**: Claude Code SDK → LiteLLM → Claude API
2. **헤드리스 모드 지원**: 비대화형 자동화 환경 지원
3. **확장 가능한 아키텍처**: 향후 마스킹/언마스킹 레이어 추가 가능
4. **컨테이너화**: Docker 기반 배포 환경

## 🏗️ 시스템 아키텍처

### 전체 구조
```
Claude Code SDK → LiteLLM Proxy Gateway → Claude API
     ↓                    ↓                    ↓
[헤드리스 모드]      [HTTP 프록시]        [실제 LLM API]
[환경변수 설정]      [요청/응답 처리]      [Claude 서비스]
   [자동화]          [로깅/모니터링]       [API 응답]
```

### 프록시 동작 원리

#### 1. 프록시 개념
프록시 서버는 클라이언트와 서버 사이에서 **중재자(intermediary)** 역할을 하는 네트워크 레이어 장치입니다.

**동작 과정:**
1. **요청 가로채기**: 클라이언트의 요청을 먼저 받음
2. **요청 처리**: 필요시 요청을 수정, 필터링, 로깅
3. **요청 전달**: 대상 서버로 요청 전송
4. **응답 처리**: 서버 응답을 받아 필요시 수정
5. **응답 반환**: 클라이언트에게 최종 응답 전송

#### 2. LiteLLM 프록시 특징
- **투명성**: Claude Code는 직접 Claude API와 통신하는 것처럼 인식
- **통합 인터페이스**: 100+ LLM을 OpenAI 호환 형태로 통일
- **중간 처리**: 요청/응답 과정에서 다양한 미들웨어 기능 수행

### HTTP 요청 변환 흐름

#### 1. 환경변수 설정
```bash
export ANTHROPIC_BASE_URL=http://localhost:4000  # LiteLLM 프록시 주소
export ANTHROPIC_AUTH_TOKEN=sk-litellm-master-key # LiteLLM 인증 키
```

#### 2. 실제 HTTP 요청 변환
```bash
# 사용자 실행
claude -p "Hello World" --model claude-3-5-sonnet

# Claude Code SDK 내부 변환 (환경변수 적용)
# 원래: https://api.anthropic.com/v1/messages
# 변경: http://localhost:4000/v1/messages
```

#### 3. HTTP 요청 형태
```http
POST http://localhost:4000/v1/messages
Authorization: Bearer sk-litellm-master-key
Content-Type: application/json

{
  "model": "claude-3-5-sonnet",
  "messages": [
    {"role": "user", "content": "Hello World"}
  ],
  "max_tokens": 1024
}
```

## 🛠️ 기술 스택 및 구현 방향

### 개발 환경
- **언어**: Python 3.10+
- **프레임워크**: FastAPI (HTTP 서버)
- **프록시 엔진**: LiteLLM (게이트웨이)
- **패키지 관리**: UV (Python 환경 관리)
- **컨테이너**: Docker Desktop
- **CI 도구**: Claude Code SDK (헤드리스 모드)

### 핵심 컴포넌트

#### 1. LiteLLM 프록시 서버
```python
# LiteLLM 설정 예시
model_list:
  - model_name: claude-3-5-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet
      api_key: os.environ/ANTHROPIC_API_KEY

general_settings:
  master_key: sk-litellm-master-key
```

#### 2. Claude Code SDK 헤드리스 모드

##### 헤드리스 모드 정의
Claude Code는 CI, pre-commit hooks, build scripts, automation과 같은 **비대화형(non-interactive)** 컨텍스트를 위한 헤드리스 모드를 포함합니다.

##### 핵심 특징
- **비대화형 실행**: `--print` (또는 `-p`) 플래그를 사용하여 최종 결과를 출력
- **세션 독립성**: 헤드리스 모드는 세션 간에 지속되지 않으며, 각 세션마다 트리거 필요
- **Unix 철학**: 구성 가능하고 스크립트 가능한 도구

##### CLI 구문 및 옵션
```bash
# 기본 헤드리스 실행
claude -p "시스템 성능 분석" \
  --append-system-prompt "당신은 성능 엔지니어입니다" \
  --allowedTools "Bash,Read,WebSearch" \
  --permission-mode acceptEdits \
  --cwd /path/to/project

# JSON 출력 형식
claude -p "코드 검토 수행" --output-format json

# 스트리밍 JSON 출력
claude -p "보안 취약점 분석" --output-format stream-json
```

##### 자동화 통합 예시
```bash
# CI 파이프라인에서 사용
claude -p "새로운 텍스트 문자열이 있으면 프랑스어로 번역하고 PR을 생성하세요"

# 로그 모니터링 자동화
tail -f app.log | claude -p "로그 스트림에서 이상 징후가 나타나면 Slack으로 알려주세요"
```

#### 3. Docker 컨테이너 환경
```dockerfile
# 기본 구조 예시
FROM python:3.10-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4000"]
```

## 📁 프로젝트 구조

```
claude-litellm-proxy/
├── config/
│   ├── litellm_config.yaml     # LiteLLM 설정
│   └── docker-compose.yml      # 컨테이너 구성
├── src/
│   ├── main.py                 # FastAPI 애플리케이션
│   ├── proxy/
│   │   ├── __init__.py
│   │   ├── server.py          # 프록시 서버 로직
│   │   └── middleware.py      # 확장 미들웨어 (향후)
│   └── utils/
│       ├── __init__.py
│       ├── logging.py         # 로깅 설정
│       └── health.py          # 헬스체크
├── tests/
│   ├── test_proxy.py          # 프록시 테스트
│   ├── test_claude_integration.py  # Claude Code 통합 테스트
│   └── test_headless.py       # 헤드리스 모드 테스트
├── scripts/
│   ├── setup.sh               # 환경 설정
│   ├── test_integration.py    # 통합 테스트 스크립트
│   └── deploy.sh              # 배포 스크립트
├── docs/
│   ├── README.md              # 프로젝트 가이드
│   ├── DEPLOYMENT.md          # 배포 가이드
│   └── API.md                 # API 문서
├── .env.example               # 환경변수 템플릿
├── requirements.txt           # Python 의존성
├── Dockerfile                 # 컨테이너 이미지
└── pyproject.toml            # 프로젝트 설정
```

## 🔧 구현 단계

### Phase 1: 기본 프록시 구축 (1주)
1. **환경 설정**
   - UV를 사용한 Python 가상환경 구성
   - Docker Desktop 설치 및 설정
   - 기본 프로젝트 구조 생성

2. **LiteLLM 프록시 서버 구현**
   - LiteLLM 기본 설정 (config.yaml)
   - FastAPI와 LiteLLM 통합
   - Claude API 연동 테스트

3. **Docker 환경 구성**
   - Dockerfile 작성
   - docker-compose.yml 설정
   - 컨테이너 기반 실행 환경

### Phase 2: Claude Code SDK 통합 (1주)
1. **환경변수 프록시 설정**
   - ANTHROPIC_BASE_URL 설정
   - ANTHROPIC_AUTH_TOKEN 설정
   - 헤드리스 모드 테스트

2. **통합 테스트**
   - 기본 대화형 모드 테스트
   - 헤드리스 모드 (`-p` 플래그) 테스트
   - JSON 출력 형식 테스트

3. **자동화 스크립트 작성**
   - Python/TypeScript SDK 활용 예제
   - CI/CD 통합 샘플

### Phase 3: 확장 및 최적화 (1주)
1. **에러 처리 및 로깅**
   - 상세 로깅 시스템 구현
   - 에러 핸들링 강화
   - 헬스체크 엔드포인트

2. **성능 최적화**
   - 응답 시간 최적화
   - 동시 요청 처리 개선
   - 메모리 사용량 최적화

3. **문서화 및 테스트**
   - API 문서 작성
   - 통합 테스트 완성
   - 배포 가이드 작성

## 🎯 중요 개발 규칙 및 코딩 표준

### 코딩 철학 및 규칙

#### 1. 절대적 오류 처리 원칙
- **절대 규칙**: 문제나 버그를 그냥 넘기지 말 것
- **즉시 중단**: 문제 발생 시 작업 중단하고 해결부터
- **목 데이터 금지**: 테스트용 가짜 데이터 생성 절대 금지

#### 2. TDD (Test-Driven Development) 적용
**올바른 TDD 순서**:
1. **Red**: 실패하는 테스트 코드 먼저 작성
2. **Green**: 테스트를 통과하는 최소한의 코드 작성  
3. **Refactor**: 코드 품질 개선 및 리팩토링

**일반적인 실수 방지**: 코드 먼저 작성 → 테스트 코드 나중 작성 (이건 TDD가 아님)

#### 3. 연속 실패 시 대응 규칙
- **2회 이상 실패**: 즉시 웹 검색으로 정확한 정보 확인
- **하드 리씽킹**: 접근 방식 전면 재검토
- **재시도**: 새로운 정보 기반으로 다시 시도

### 코드 품질 관리 자동화

#### 1. Big Code 문제 해결
- **500라인 제한**: 파일이 500라인 초과 시 LLM이 컨텍스트 잃기 시작
- **자동 분리**: 무결성 유지하면서 코드 자동 분리
- **모듈화**: 기능별로 적절히 분할

#### 2. Dead Code 제거
- **자동 감지**: 사용하지 않는 변수, 함수 자동 탐지
- **정리**: 불필요한 코드 자동 제거
- **최적화**: 코드베이스 정리

#### 3. 테스트 커버리지 관리
- **유닛 테스트**: 코드 변경 시 테스트 커버리지 유지
- **자동 보완**: 커버리지 하락 시 자동으로 테스트 추가
- **품질 보장**: 지속적인 코드 품질 유지

### Python 코딩 표준

#### 1. 코드 스타일
```python
# UV 환경 관리 사용
# 의존성 충돌 방지를 위해 글로벌 설치 금지
# 가상환경 필수 사용

# 함수명: snake_case
def process_claude_request():
    pass

# 클래스명: PascalCase
class LiteLLMProxy:
    pass

# 상수: UPPER_SNAKE_CASE
MAX_REQUEST_SIZE = 1024
```

#### 2. 에러 처리
```python
# 모든 외부 API 호출에 에러 처리 필수
try:
    response = await claude_api_call()
except Exception as e:
    logger.error(f"Claude API 호출 실패: {e}")
    raise HTTPException(status_code=500, detail="API 호출 실패")
```

#### 3. 비동기 처리
```python
# FastAPI에서 비동기 함수 사용
async def proxy_request(request: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=request)
        return response.json()
```

## 📋 테스트 전략

### 테스트 레벨

#### 1. 단위 테스트 (Unit Tests)
```python
# pytest 사용
def test_litellm_config_validation():
    """LiteLLM 설정 파일 검증 테스트"""
    pass

def test_request_transformation():
    """요청 변환 로직 테스트"""
    pass
```

#### 2. 통합 테스트 (Integration Tests)
```python
def test_claude_code_integration():
    """Claude Code SDK 통합 테스트"""
    pass

def test_headless_mode():
    """헤드리스 모드 동작 테스트"""
    pass
```

#### 3. 엔드투엔드 테스트 (E2E Tests)
```bash
# 실제 Claude Code 명령 실행 테스트
claude -p "Hello World" --output-format json
```

### 성능 테스트
- **로드 테스트**: 동시 요청 처리 능력
- **스트레스 테스트**: 한계 상황에서의 안정성
- **지연 시간 테스트**: 응답 시간 측정

## 🚀 배포 및 운영

### 배포 환경
- **개발**: Docker Compose로 로컬 환경
- **스테이징**: 클라우드 컨테이너 환경
- **프로덕션**: 확장 가능한 컨테이너 오케스트레이션

### 모니터링
- **헬스체크**: `/health` 엔드포인트
- **메트릭스**: 요청 수, 응답 시간, 에러 율
- **로깅**: 구조화된 JSON 로그

### 보안
- **API 키 관리**: 환경변수로 민감 정보 보호
- **요청 제한**: Rate limiting 적용
- **입력 검증**: 모든 입력 데이터 검증

## 🔮 확장 계획

### 향후 기능 (Phase 4+)
1. **마스킹/언마스킹 레이어**
   - 민감한 데이터 자동 마스킹
   - 응답 시 언마스킹 처리
   - 정규식 기반 패턴 매칭

2. **고급 라우팅**
   - 모델별 라우팅 규칙
   - 로드밸런싱 및 폴백
   - 지역별 엔드포인트 분산

3. **관리 대시보드**
   - 실시간 모니터링 UI
   - 설정 관리 인터페이스
   - 사용량 통계 및 분석

## 📊 성공 지표

### 기술적 지표
- **응답 시간**: 평균 200ms 이하
- **가용성**: 99.9% 업타임
- **처리량**: 초당 100+ 요청 처리

### 비즈니스 지표
- **아키텍처 단순화**: 기존 대비 컴포넌트 50% 감소
- **개발 효율성**: 새 기능 추가 시간 30% 단축
- **유지보수 비용**: 월 운영 시간 40% 절약

## 📚 참고 자료

### 공식 문서
- [LiteLLM 공식 문서](https://docs.litellm.ai/)
- [Claude Code SDK 문서](https://docs.anthropic.com/en/docs/claude-code/sdk)
- [FastAPI 문서](https://fastapi.tiangolo.com/)

### 기술 스택 가이드
- [UV 패키지 관리자](https://github.com/astral-sh/uv)
- [Docker 컨테이너 가이드](https://docs.docker.com/)
- [pytest 테스팅 프레임워크](https://docs.pytest.org/)

## 🏁 결론

이 프로젝트는 Claude Code SDK와 LiteLLM을 통합한 현대적이고 확장 가능한 프록시 시스템을 구축합니다. 단계별 구현과 철저한 테스트를 통해 안정적이고 효율적인 시스템을 완성하며, 향후 마스킹 레이어 등의 고급 기능을 추가할 수 있는 확장 가능한 아키텍처를 제공합니다.

**핵심 가치**: 복잡성 제거, 개발 효율성 증대, 미래 확장성 확보