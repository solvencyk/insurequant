# Markdown -> kics_data.json 변환 절차

## 목표

품질 게이트를 통과한 Markdown을 표준 스키마로 정규화하여 단일 산출물 `kics_data.json`을 생성합니다.

## 모듈

- 변환: `src/solvency/transform/md_to_json.py`
- 스키마: `schemas/kics_data.schema.json`
- 검증: `src/solvency/validation/schema.py`

## 단계

1. `md_inbox/<companyCode>/*.md`를 순회
2. Front Matter 파싱(메타데이터 확보)
3. 표 행에서 KICS 핵심 항목 식별(`METRIC_ID_BY_ROW` 매핑 사용)
4. 숫자 정규화(쉼표/괄호/대시/단위 분리)
5. UPSERT 키 `(company_code, fiscal_year, quarter, metric_id)`로 머지
6. 정렬 후 `kics_data.json` 저장
7. 옵션: `SOLVENCY_LEGACY_JSON_ALIAS`가 설정되어 있으면 동일 내용을 alias로 추가 기록

## 표준 레코드 스키마

```json
{
  "company_code": "KR0008",
  "fiscal_year": "FY24",
  "quarter": "Q4",
  "disclosure_date": "2025-03-31",
  "metric_id": "solvency_ratio",
  "metric_name_ko": "다. 지급여력비율",
  "value": 178.4,
  "unit": "%",
  "source_type": "docling_markdown",
  "source_file": "KR0008_FY24_Q4_2025-03-31.md",
  "parse_confidence": 0.93,
  "created_at": "2026-04-25T22:00:00+00:00"
}
```

## metric_id 매핑

- `solvency_amount` ← `가. 지급여력금액`
- `tier1_capital` ← `기본자본`
- `tier2_capital` ← `보완자본`
- `required_capital` ← `나. 지급여력기준금액`
- `solvency_ratio` ← `다. 지급여력비율`

## 숫자 정규화

- `12,345` → `12345`
- `(1,234)` → `-1234`
- `—`, `-`, 빈값 → `null`
- `178.4 %` → 값 `178.4`, `unit="%"`

## 멱등성

- 동일 입력 두 번 빌드 시 `kics_data.json`의 SHA256 동일 (Stage 6-3 게이트가 강제)
- 정렬 키: `(company_code, fiscal_year, quarter, metric_id)`
- `created_at`은 한 번의 빌드 안에서 모든 레코드 동일 값으로 부여(빌드별 reproducible)

## 검증 포인트

- 회사코드/기준일/분기 누락 금지
- 핵심 항목 최소 3개 존재
- 중복 키 금지
- 비율 재계산: `solvency_amount / required_capital * 100 ≈ solvency_ratio` (허용 오차 1.0)

## K-ICS disclosure JSON gate

After building or updating root `kics_disclosure.json`:

1. Run `python scripts/validate_kics_disclosure.py`
2. **RED=0** required before template sync / HTML deploy (see [`kics-json-validation-rules.md`](kics-json-validation-rules.md))
3. Documented exceptions only in `TODO.md`; otherwise treat RED as parsing failure

Rules cover items 1-8, post-transition ratio (`8_post`), and life sub-risk R7 (`8_life`); tolerance default 2.0.

## 산출물

- 최종: `kics_data.json`
- alias(옵션): `insurance_data.json` (deprecation 로그 포함)
- 리포트: `artifacts/reports/harness_data_<run_id>.json`
