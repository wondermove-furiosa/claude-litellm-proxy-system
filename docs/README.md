# Documentation

이 폴더는 Claude LiteLLM Proxy 프로젝트의 모든 문서를 체계적으로 분류하여 보관합니다.

## 📁 폴더 구조

### 📊 reports/
**분석 보고서 및 연구 결과**
- `COMPREHENSIVE_ANALYSIS_REPORT.md` - 종합 분석 보고서
- `FINAL-LEGACY-CONFLICT-ANALYSIS-REPORT.md` - 최종 레거시 충돌 분석 보고서
- `conflict-examples-detailed.md` - 충돌 상황 구체적 예시 및 근거 데이터
- `improvement-justification.md` - 개선사항 정당성 및 검증 결과
- `ref-legacy-conflict-analysis.md` - 기존 레퍼런스 충돌 문제점 분석

### 📋 specifications/
**명세서 및 규칙 문서**
- `MASKING_RULES.md` - 마스킹 규칙 정의
- `ref-masking-rule.md` - 레퍼런스 마스킹 규칙 (우선순위 포함)
- `masking-rule-checklist.md` - 마스킹 규칙 체크리스트

### 🚀 development/
**개발 관련 문서**
- `PLAN.md` - 프로젝트 개발 계획
- `pattern_alignment_fixes.md` - 패턴 정렬 수정사항

### 🗄️ archive/
**기타 및 참조 문서**
- 향후 추가될 아카이브 문서들

## 📖 문서 활용 가이드

### 프로젝트 이해를 위한 추천 읽기 순서

1. **프로젝트 개요 파악**
   - `development/PLAN.md` - 전체 프로젝트 방향성 이해

2. **마스킹 규칙 이해**
   - `specifications/MASKING_RULES.md` - 기본 마스킹 규칙
   - `specifications/ref-masking-rule.md` - 상세한 우선순위 체계
   - `specifications/masking-rule-checklist.md` - 규칙 준수 체크리스트

3. **기술적 분석 이해**
   - `reports/COMPREHENSIVE_ANALYSIS_REPORT.md` - 전체적인 기술 분석
   - `reports/FINAL-LEGACY-CONFLICT-ANALYSIS-REPORT.md` - 레거시 시스템 문제점과 해결방안

4. **상세한 기술 구현**
   - `reports/conflict-examples-detailed.md` - 구체적인 충돌 사례
   - `reports/improvement-justification.md` - 개선사항 정당성
   - `development/pattern_alignment_fixes.md` - 패턴 수정 내역

## 🔍 문서 검색 팁

- **보고서**: 분석 결과와 연구 내용은 `reports/` 폴더에서 찾아보세요
- **규칙/명세**: 마스킹 규칙과 시스템 명세는 `specifications/` 폴더를 확인하세요
- **개발 가이드**: 개발 관련 정보는 `development/` 폴더를 참조하세요

## 📝 문서 기여하기

새로운 문서를 추가할 때는 다음 분류 기준을 따라주세요:

- **분석/연구 결과** → `reports/`
- **시스템 명세/규칙** → `specifications/`
- **개발 관련 정보** → `development/`
- **기타/참조 자료** → `archive/`