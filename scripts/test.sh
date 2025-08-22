#!/bin/bash

# Claude LiteLLM Proxy - TDD 테스트 실행 스크립트
# Mock 절대 금지, 핵심 기능만 테스트

set -e

echo "🧪 TDD 테스트 실행 - Red-Green-Refactor"

# 가상환경 확인
if [ ! -d ".venv" ]; then
    echo "❌ 가상환경이 없습니다. scripts/setup.sh를 먼저 실행하세요."
    exit 1
fi

# 환경 변수 로드
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "📋 테스트 전 코드 품질 검사..."

# 1. 코드 포맷팅 확인
echo "  → 코드 포맷팅 (Black)"
uv run black --check src/ tests/ || {
    echo "⚠️  코드 포맷팅 필요. 다음 명령 실행: uv run black src/ tests/"
    exit 1
}

# 2. Import 정리 확인
echo "  → Import 정리 (isort)"
uv run isort --check-only src/ tests/ || {
    echo "⚠️  Import 정리 필요. 다음 명령 실행: uv run isort src/ tests/"
    exit 1
}

# 3. 타입 체크
echo "  → 타입 체크 (mypy)"
uv run mypy src/ || {
    echo "❌ 타입 에러가 있습니다. 수정 후 다시 테스트하세요."
    exit 1
}

echo "✅ 코드 품질 검사 통과"
echo ""

# 4. 실제 테스트 실행 (Mock 금지)
echo "🚨 핵심 기능 테스트 실행 (Mock 금지 원칙)"
echo "   - 실제 Redis 연결 필요"
echo "   - 실제 패턴 매칭만 테스트"
echo "   - 의미 있는 검증만 수행"
echo ""

# 테스트 실행
uv run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

echo ""
echo "📊 테스트 결과:"
echo "   - 커버리지 리포트: htmlcov/index.html"
echo "   - 실패한 테스트가 있다면 즉시 수정 필요 (다음 단계 진행 금지)"