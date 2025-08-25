# Tests

이 폴더는 Claude LiteLLM Proxy 프로젝트의 모든 테스트 코드와 결과를 포함합니다.

## 📁 폴더 구조

### 🔄 overlap/
충돌 해결 관련 테스트
- `test_overlap_detection.py` - Overlap Detection Engine 기능 테스트
- `test_overlap_detection_fixed.py` - 수정된 충돌 해결 테스트

### 🎯 patterns/
패턴 검증 관련 테스트
- `test_missing_patterns.py` - 누락 패턴 감지 테스트
- `test_phase3_patterns.py` - Phase 3 패턴 검증 테스트
- `test_priority_validation.py` - 우선순위 검증 테스트
- `extract_all_patterns.py` - 모든 패턴 추출 유틸리티

### ✅ compliance/
레퍼런스 준수 관련 테스트
- `test_ref_compliance_100.py` - ref-masking-rule.md 100% 준수 검증

### 🔗 integration/
API/통합 테스트
- `test_claude_api_integration.py` - Claude API 통합 테스트

### 🏭 production/
프로덕션 준비 테스트
- `test_production_masking.py` - 프로덕션 마스킹 테스트
- `final_production_verification.py` - 최종 프로덕션 검증

### 🛠️ utilities/
테스트 유틸리티
- `comprehensive_test_framework.py` - 종합 테스트 프레임워크
- `debug_masking.py` - 마스킹 디버깅 유틸리티

### 📊 results/
테스트 결과 JSON 파일들
- `comprehensive-test-results.json` - 종합 테스트 결과
- `pattern-verification-results.json` - 패턴 검증 결과
- `pattern-analysis-results.json` - 패턴 분석 결과
- `production-verification-results.json` - 프로덕션 검증 결과
- `production-readiness-results.json` - 프로덕션 준비도 결과
- `production-test-results.json` - 프로덕션 테스트 결과
- `compliance-test-results.json` - 준수도 테스트 결과

## 🚀 테스트 실행

### 전체 테스트 실행
```bash
python -m pytest tests/
```

### 카테고리별 테스트 실행
```bash
# 충돌 해결 테스트
python -m pytest tests/overlap/

# 패턴 검증 테스트
python -m pytest tests/patterns/

# 준수도 테스트
python -m pytest tests/compliance/

# 통합 테스트
python -m pytest tests/integration/

# 프로덕션 테스트
python -m pytest tests/production/
```

### 개별 테스트 실행
```bash
# 특정 테스트 파일 실행
python tests/overlap/test_overlap_detection.py
```

## 📈 테스트 결과 확인

테스트 실행 후 결과는 `results/` 폴더에 JSON 형식으로 저장됩니다. 각 결과 파일은 해당하는 테스트의 상세한 분석 정보를 포함합니다.