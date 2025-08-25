# Test Results

이 폴더는 각종 테스트 실행 결과를 JSON 형식으로 보관합니다.

## 📊 결과 파일 목록

### 📈 comprehensive-test-results.json
**종합 테스트 결과**
- 소스: `tests/utilities/comprehensive_test_framework.py`
- 내용: 전체 시스템의 종합적인 테스트 결과
- 포함 항목: 성능 지표, 패턴 매칭 성공률, 오류 분석

### 🎯 pattern-verification-results.json
**패턴 검증 결과**
- 소스: `tests/patterns/` 폴더의 패턴 검증 테스트들
- 내용: 코어 패턴들의 동작 검증 결과
- 포함 항목: 패턴별 성공률, 실패 사례, 검증 메트릭

### 🔍 pattern-analysis-results.json
**패턴 분석 결과**
- 소스: `tests/patterns/extract_all_patterns.py`
- 내용: 전체 58개 패턴의 상세 분석 결과
- 포함 항목: 패턴 정의, 우선순위, 검증 함수 유무, 테스트 샘플

### 🏭 production-verification-results.json
**프로덕션 검증 결과**
- 소스: `tests/production/final_production_verification.py`
- 내용: 최종 프로덕션 환경 준비도 검증 결과
- 포함 항목: 시스템 안정성, 성능 벤치마크, 보안 검증

### 🛠️ production-readiness-results.json
**프로덕션 준비도 결과**
- 소스: 프로덕션 준비도 평가 테스트
- 내용: 운영 환경 배포 준비도 평가
- 포함 항목: 인프라 체크, 보안 정책, 모니터링 설정

### 📊 production-test-results.json
**프로덕션 테스트 결과**
- 소스: `tests/production/test_production_masking.py`
- 내용: 프로덕션 환경에서의 마스킹 동작 테스트
- 포함 항목: 실제 데이터 처리 결과, 성능 지표, 오류율

### ✅ compliance-test-results.json
**준수도 테스트 결과**
- 소스: `tests/compliance/test_ref_compliance_100.py`
- 내용: ref-masking-rule.md 기준 100% 준수도 검증
- 포함 항목: 
  - 전체 준수율: 98.15% (106/108 테스트 통과)
  - 우선순위 준수: 96.08% (49/51 패턴)
  - 기능 테스트: 100% (51/51 패턴)
  - 충돌 해결: 100% (3/3 시나리오)

## 📖 결과 파일 읽는 법

### JSON 구조 예시
```json
{
  "timestamp": "2025-08-25T12:00:00Z",
  "overall_compliance": 98.15,
  "total_tests": 108,
  "passed_tests": 106,
  "failed_tests": 2,
  "test_results": {
    "category1": { "details": "..." },
    "category2": { "details": "..." }
  }
}
```

### 주요 메트릭 해석

- **overall_compliance**: 전체 준수율 (%)
- **success_rate**: 성공률 (%)
- **processing_time**: 처리 시간 (초)
- **pattern_matches**: 패턴 매칭 개수
- **conflicts_resolved**: 해결된 충돌 개수

## 🔄 결과 업데이트

테스트를 실행할 때마다 해당 결과 파일이 자동으로 업데이트됩니다. 이전 결과는 덮어쓰여지므로 필요시 백업을 권장합니다.

## 📈 결과 활용

- **개발 과정**: 각 테스트 결과를 통해 시스템 개선점 파악
- **품질 보증**: 준수도 및 성능 지표를 통한 품질 관리
- **배포 결정**: 프로덕션 준비도 결과를 바탕으로 배포 여부 결정
- **문제 해결**: 실패한 테스트 케이스 분석을 통한 버그 수정