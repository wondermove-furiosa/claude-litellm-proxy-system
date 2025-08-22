#!/bin/bash

# Claude LiteLLM Proxy - UV 환경 설정 스크립트
# TDD 방식 개발 환경 구축

set -e  # 에러 발생 시 즉시 중단

echo "🚀 Claude LiteLLM Proxy - UV 환경 설정 시작"

# UV 설치 확인
if ! command -v uv &> /dev/null; then
    echo "❌ UV가 설치되지 않았습니다."
    echo "   설치 명령: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ UV 버전: $(uv --version)"

# Python 3.11 가상환경 생성 (이미 있으면 스킵)
if [ ! -d ".venv" ]; then
    echo "📦 Python 3.11 가상환경 생성..."
    uv venv --python 3.11
else
    echo "✅ 가상환경이 이미 존재합니다."
fi

# 의존성 설치
echo "📦 의존성 설치..."
uv sync --extra dev

# 환경 변수 템플릿 생성 (없을 경우만)
if [ ! -f ".env" ]; then
    echo "📝 환경 변수 템플릿 생성..."
    cat > .env << EOF
# Claude LiteLLM Proxy 환경 변수
ANTHROPIC_API_KEY=your-claude-api-key-here
ANTHROPIC_BASE_URL=http://localhost:4000
ANTHROPIC_AUTH_TOKEN=sk-litellm-master-key

# Redis 설정
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# 개발 환경 설정
ENVIRONMENT=development
LOG_LEVEL=DEBUG
EOF
    echo "⚠️  .env 파일을 편집하여 API 키를 설정하세요."
else
    echo "✅ .env 파일이 이미 존재합니다."
fi

# 가상환경 활성화 안내
echo ""
echo "🎉 설정 완료!"
echo ""
echo "다음 명령으로 가상환경을 활성화하세요:"
echo "  source .venv/bin/activate"
echo ""
echo "TDD 개발 시작:"
echo "  uv run pytest tests/         # 테스트 실행"
echo "  uv run black src/ tests/     # 코드 포맷팅"
echo "  uv run mypy src/             # 타입 체크"
echo ""