#!/bin/bash

# Claude LiteLLM Proxy - 개발 서버 실행 스크립트

set -e

echo "🚀 Claude LiteLLM Proxy 개발 서버 시작"

# 가상환경 활성화 확인
if [ ! -d ".venv" ]; then
    echo "❌ 가상환경이 없습니다. scripts/setup.sh를 먼저 실행하세요."
    exit 1
fi

# 환경 변수 로드
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 개발 서버 실행 (핫리로드 지원)
echo "📡 FastAPI 개발 서버 실행 중..."
echo "   URL: http://localhost:8000"
echo "   중지: Ctrl+C"
echo ""

uv run uvicorn src.claude_litellm_proxy.main:app --host 0.0.0.0 --port 8000 --reload