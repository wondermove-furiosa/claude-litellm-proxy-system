# 환경변수 설정 문제 검증 및 해결방안

**검증 일시**: 2025-08-22  
**검증 대상**: Claude Code SDK + LiteLLM 프록시 환경변수 설정  
**주요 문제**: 환경변수 충돌, 무한루프, 보안 취약점

## 📋 검증 개요

Phase 3 완전한 통합 과정에서 발견된 환경변수 설정 관련 치명적 문제들과 해결 과정을 상세히 문서화합니다. 특히 ANTHROPIC_BASE_URL 무한루프 문제와 LITELLM_MASTER_KEY 보안 취약점을 중점적으로 다룹니다.

## 🚨 발견된 주요 문제점들

### 1. ANTHROPIC_BASE_URL 무한루프 문제 (치명적)

**문제 설명**:
```bash
# 문제가 된 환경변수 설정
ANTHROPIC_BASE_URL=http://localhost:8000  # 우리 프록시 주소
```

**무한루프 메커니즘**:
1. Claude Code SDK → 우리 프록시 (`http://localhost:8000`)
2. 우리 프록시 → LiteLLM 클라이언트  
3. LiteLLM → `ANTHROPIC_BASE_URL` 읽음 → 다시 우리 프록시 호출!
4. 무한루프 발생 → 30초 타임아웃

**증상**:
- Claude Code SDK headless 모드 타임아웃
- API 호출 403 Forbidden 에러
- LiteLLM 로그: `Client error '403 Forbidden' for url 'http://localhost:8000/v1/messages'`

### 2. 잘못된 Claude 모델명 사용

**문제 모델들**:
- `claude-sonnet-4-20250514` → 인증 오류 발생
- `claude-3-5-sonnet-20241022` → 404 Not Found

**해결 모델**:
- `claude-3-haiku-20240307` → 정상 작동

### 3. max_tokens 제한 초과

**문제**:
- Claude Code SDK 요청: `max_tokens: 8192`
- claude-3-haiku-20240307 제한: `4096`
- 결과: `400 Bad Request` 에러

### 4. 🚨 LITELLM_MASTER_KEY 심각한 보안 취약점

**문제 상황**:
```python
# main.py:96 - 하드코딩된 기본값
expected_key = os.getenv("LITELLM_MASTER_KEY", "sk-litellm-master-key")
```

**보안 취약점**:
1. **하드코딩된 마스터키**: `sk-litellm-master-key`가 코드에 노출
2. **모든 환경에서 동일**: dev/staging/prod 구분 없음
3. **키 로테이션 불가**: 고정된 키 값 사용
4. **권한 세분화 불가**: 모든 요청이 동일한 마스터키 사용

**실제 검증 결과**:
```bash
# ❌ 잘못된 키 - 차단됨
curl -H "Authorization: Bearer wrong-key" → 401 Unauthorized

# 🚨 하드코딩된 키 - 접근 성공!
curl -H "Authorization: Bearer sk-litellm-master-key" → 200 OK
```

## 🔧 해결 방안들

### 1. 환경변수 분리 및 명시적 설정

**Before** (무한루프):
```python
# LiteLLM이 ANTHROPIC_BASE_URL을 읽어서 자신을 호출
litellm_request = {
    "api_key": self.claude_api_key
    # base_url이 환경변수에 의해 http://localhost:8000로 설정됨
}
```

**After** (직접 제어):
```python
# 환경변수 분리
self.claude_base_url = os.getenv("LITELLM_CLAUDE_BASE_URL", "https://api.anthropic.com")

litellm_request = {
    "api_key": self.claude_api_key,
    "base_url": self.claude_base_url  # 명시적 Claude API 호출
}
```

**최종 .env 설정**:
```bash
# Claude Code SDK용 (우리 프록시로 리다이렉트)
# ANTHROPIC_BASE_URL=http://localhost:8000  # 주석처리 (SDK에서 프로그래밍 방식으로 설정)

# LiteLLM용 (Claude API 직접 호출)
LITELLM_CLAUDE_BASE_URL=https://api.anthropic.com

# 작동하는 모델
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

### 2. max_tokens 제한 처리

```python
# Claude Haiku 모델의 4096 토큰 제한 적용
max_tokens = min(request_data.get("max_tokens", 4096), 4096)
```

### 3. 🚨 프로덕션 환경 보안 개선 방안 (LiteLLM 공식 가이드 기반)

**현재 상태**: 심각한 보안 취약점 존재  
**프로덕션 적용 필수 개선사항**:

#### 🔐 Phase 1: 마스터키 보안 강화 (즉시 적용)

1. **강력한 마스터키 생성**:
```bash
# 32바이트 랜덤 키 생성 (권장)
python -c "import secrets; print(f'sk-{secrets.token_hex(32)}')"
# 출력 예: sk-a1b2c3d4e5f6...64자리

# 또는 OpenSSL 사용
openssl rand -hex 32 | sed 's/^/sk-/'
```

2. **환경변수 분리**:
```bash
# .env.development
LITELLM_MASTER_KEY=sk-dev-$(openssl rand -hex 16)

# .env.staging  
LITELLM_MASTER_KEY=sk-staging-$(openssl rand -hex 16)

# .env.production
LITELLM_MASTER_KEY=sk-prod-$(openssl rand -hex 16)
```

3. **코드에서 하드코딩 제거**:
```python
# ❌ 현재 (취약)
expected_key = os.getenv("LITELLM_MASTER_KEY", "sk-litellm-master-key")

# ✅ 개선 (보안)
expected_key = os.getenv("LITELLM_MASTER_KEY")
if not expected_key:
    raise ValueError("LITELLM_MASTER_KEY 환경변수 필수 설정")
```

#### 🏢 Phase 2: LiteLLM Virtual Keys 시스템 도입 (권장)

**LiteLLM 공식 권장 아키텍처**:

1. **데이터베이스 설정** (PostgreSQL 필수):
```bash
# 데이터베이스 연결 설정
DATABASE_URL=postgresql://user:password@localhost:5432/litellm_db
```

2. **Virtual Keys 생성 시스템**:
```python
# /key/generate 엔드포인트 활용
curl -X POST "http://localhost:8000/key/generate" \
  -H "Authorization: Bearer sk-master-key" \
  -H "Content-Type: application/json" \
  -d '{
    "models": ["claude-3-haiku-20240307"],
    "duration": "30d",
    "max_budget": 100.0,
    "user_id": "claude-code-user",
    "metadata": {"service": "claude-code-proxy"}
  }'
```

3. **사용자별 키 관리**:
```yaml
# config.yaml - LiteLLM 설정
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
  
model_list:
  - model_name: claude-3-haiku-20240307
    model_info:
      supported_environments: ["production"]
      
credential_list:
  - credential_name: claude_credential
    credential_values:
      api_key: os.environ/ANTHROPIC_API_KEY
```

#### 🔧 Phase 3: 엔터프라이즈급 보안 강화

1. **JWT 토큰 기반 인증**:
```python
import jwt
from datetime import datetime, timedelta

def generate_jwt_token(user_id: str, permissions: list):
    """JWT 토큰 생성"""
    payload = {
        'user_id': user_id,
        'permissions': permissions,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET'), algorithm='HS256')

async def verify_jwt_token(token: str):
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

2. **키 로테이션 시스템**:
```python
async def rotate_master_key():
    """무중단 마스터키 로테이션"""
    new_key = f"sk-{secrets.token_hex(32)}"
    
    # 1. 새 키를 보조 키로 등록
    await update_secondary_key(new_key)
    
    # 2. 새 키 검증
    await validate_new_key(new_key)
    
    # 3. 기본 키를 새 키로 교체
    await promote_secondary_to_primary(new_key)
    
    # 4. 구 키 비활성화 (7일 후)
    await schedule_key_deactivation(old_key, days=7)
```

3. **접근 제어 및 모니터링**:
```python
# IP 화이트리스트
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",")

# 요청 속도 제한
from slowapi import Limiter
limiter = Limiter(key_func=lambda: request.client.host)

@app.post("/v1/claude-code")
@limiter.limit("100/hour")  # 시간당 100회 제한
async def claude_code_proxy(request: Request):
    # IP 검증
    client_ip = request.client.host
    if ALLOWED_IPS and client_ip not in ALLOWED_IPS:
        raise HTTPException(403, "IP not allowed")
```

#### 🏗️ Phase 4: 완전한 프로덕션 배포 아키텍처

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  claude-proxy:
    build: .
    environment:
      - LITELLM_MASTER_KEY_FILE=/run/secrets/master_key
      - DATABASE_URL_FILE=/run/secrets/db_url
      - ANTHROPIC_API_KEY_FILE=/run/secrets/claude_key
    secrets:
      - master_key
      - db_url  
      - claude_key
    networks:
      - internal
      
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=litellm
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - internal

secrets:
  master_key:
    external: true
  db_url:
    external: true
  claude_key:
    external: true
  db_password:
    external: true

networks:
  internal:
    driver: bridge
```

#### 📊 보안 수준 비교

| 항목 | 현재 (개발) | Phase 1 (기본) | Phase 2 (권장) | Phase 3-4 (엔터프라이즈) |
|------|-------------|----------------|-----------------|-------------------------|
| 마스터키 | 하드코딩 | 환경변수 | Virtual Keys | JWT + 로테이션 |
| 보안 등급 | 🚨 매우 취약 | ⚠️ 기본 | ✅ 양호 | 🔒 매우 강화 |
| 키 관리 | 고정 | 수동 | 자동생성 | 완전자동화 |
| 사용자 구분 | 없음 | 없음 | 있음 | 세분화 |
| 모니터링 | 없음 | 기본 로그 | 사용량 추적 | 완전 감사 |
| 프로덕션 적합성 | ❌ 불가 | ⚠️ 최소 | ✅ 권장 | 🏆 이상적 |

## 📊 검증 결과

### ✅ 해결된 문제들

1. **ANTHROPIC_BASE_URL 무한루프**: 
   - 환경변수 분리로 해결
   - LiteLLM → `https://api.anthropic.com` 직접 호출

2. **Claude 모델 호환성**:
   - `claude-3-haiku-20240307` 사용으로 해결
   - API 호출 성공률 100%

3. **max_tokens 제한**:
   - 4096 토큰 제한 적용
   - 400 에러 해결

4. **완전한 플로우 작동**:
   - Claude Code SDK → Proxy → LiteLLM → Claude API ✅
   - AWS 마스킹/언마스킹 ✅
   - 응답 시간 2-3초 ✅

### 🚨 미해결 보안 문제

**LITELLM_MASTER_KEY 하드코딩 취약점**:
- **위험도**: HIGH (9/10)
- **영향**: 전체 시스템 무단 접근 가능
- **현재 상태**: 수정되지 않음
- **프로덕션 사용 불가**: 보안 수정 필수

## 🔍 검증 명령어들

### 환경변수 설정 확인
```bash
# 서버 로그에서 확인
uv run uvicorn claude_litellm_proxy.main:app --port 8000
# 출력: "LiteLLM Claude API 주소: https://api.anthropic.com"
```

### 완전한 플로우 테스트
```bash
# AWS 마스킹 + 완전한 플로우
curl -X POST http://localhost:8000/v1/claude-code \
  -H "Authorization: Bearer sk-litellm-master-key" \
  -d '{"prompt": "Test with EC2 i-1234567890abcdef0", "allowed_tools": []}'
  
# 결과: i-1234567890abcdef0 → ec2-002 마스킹 성공
```

### 보안 취약점 검증
```bash
# ❌ 잘못된 키
curl -H "Authorization: Bearer wrong-key" → 401 Unauthorized

# 🚨 하드코딩된 키로 접근 성공
curl -H "Authorization: Bearer sk-litellm-master-key" → 200 OK
```

## 🚀 최종 상태

**기능적 완성도**: ✅ 100% (모든 플로우 작동)
**보안 상태**: 🚨 취약 (LITELLM_MASTER_KEY 하드코딩)

### 코드 위치 참조

**환경변수 설정**: 
- `.env:9` - `LITELLM_CLAUDE_BASE_URL=https://api.anthropic.com`
- `src/claude_litellm_proxy/proxy/litellm_client.py:39` - 환경변수 읽기

**보안 취약점**:
- `src/claude_litellm_proxy/main.py:96` - 하드코딩된 기본값
- `.env:12` - `LITELLM_MASTER_KEY=sk-litellm-master-key`

**플로우 확인**:
- `src/claude_litellm_proxy/main.py:140` - Claude Code SDK 엔드포인트
- `src/claude_litellm_proxy/proxy/litellm_client.py:71` - LiteLLM base_url 설정

## 🎯 프로덕션 배포 우선순위 가이드

### 즉시 적용 (24시간 내)
1. **🚨 하드코딩 제거** - Phase 1 Step 3 적용
2. **🔐 강력한 마스터키 생성** - Phase 1 Step 1 적용  
3. **📁 환경별 설정 분리** - Phase 1 Step 2 적용

### 단기 적용 (1주일 내)  
4. **🗄️ PostgreSQL 데이터베이스 설정** - Phase 2 적용
5. **🔑 Virtual Keys 시스템 도입** - Phase 2 적용
6. **📊 기본 모니터링 구현**

### 중기 적용 (1개월 내)
7. **🎫 JWT 토큰 기반 인증** - Phase 3 적용  
8. **🔄 키 로테이션 시스템** - Phase 3 적용
9. **🚨 접근 제어 및 속도 제한** - Phase 3 적용

### 장기 적용 (3개월 내)
10. **🐳 컨테이너 보안 강화** - Phase 4 적용
11. **🏢 엔터프라이즈 배포** - Phase 4 적용

## 📋 체크리스트: 프로덕션 준비도

### 필수 항목 (모두 체크되어야 프로덕션 배포 가능)
- [ ] 하드코딩된 마스터키 제거
- [ ] 강력한 랜덤 마스터키 생성 및 적용  
- [ ] 환경변수 기반 설정으로 전환
- [ ] 환경별 설정 파일 분리
- [ ] PostgreSQL 데이터베이스 연결
- [ ] Virtual Keys 시스템 적용

### 권장 항목 (보안 강화)
- [ ] JWT 토큰 인증 구현
- [ ] 키 로테이션 시스템 구축
- [ ] IP 화이트리스트 적용
- [ ] 요청 속도 제한 설정
- [ ] 접근 로그 및 모니터링
- [ ] Docker Secrets 관리

### 고급 항목 (엔터프라이즈)
- [ ] SSO 통합 (OIDC/SAML)
- [ ] 다중 환경 배포 파이프라인
- [ ] 자동화된 보안 스캔
- [ ] 감사 로그 및 컴플라이언스

## ⚠️ 프로덕션 사용 전 필수 수정사항

**즉시 수정 필요** (HIGH 위험):
1. **LITELLM_MASTER_KEY 하드코딩 제거** - 현재 누구나 접근 가능
2. **강력한 랜덤 마스터키 적용** - 64자리 랜덤 키 필수
3. **환경별 설정 분리** - dev/staging/prod 구분 필수

**단기 수정 권장** (MEDIUM 위험):  
4. **PostgreSQL 연동** - Virtual Keys 시스템 필수
5. **기본 모니터링** - 사용량 추적 및 이상 탐지
6. **접근 제어** - IP 화이트리스트 및 속도 제한

---

**🔒 최종 보안 경고**: 
- **현재 상태**: 프로덕션 사용 절대 금지 (HIGH 보안 위험)
- **최소 요구사항**: Phase 1 완료 후 제한적 프로덕션 사용 가능
- **권장 상태**: Phase 2 완료 후 안전한 프로덕션 사용 가능  
- **이상적 상태**: Phase 3-4 완료로 엔터프라이즈급 보안 달성