# Agent: K-ICS Data Pipeline

**목표:** 생명/손해보험사 분기별 K-ICS 경영공시 자료(PDF) 수집, 지표 파싱, 검증 및 `kics_data.json` 통합.

## 1. 수집 (Sourcing) 원칙
- **플로우 참고:** `claude-download-flow.md` 기반으로 작동.
- 생보사는 생명보험협회 일괄 다운로드, 손보사는 회사별 공시실 접속 및 ZIP 압축 해제 후 '정기경영공시' 추출.
- **[Fail-fast 방어]:** 손보사 홈페이지의 보안(Anti-bot)으로 스크래핑이 막힐 경우, 우회하려고 무한 삽질하지 말 것. **즉시 중단하고 사용자에게 해당 회사의 다운로드 실패를 알린 뒤 직접 파일이나 링크를 요청할 것.**

## 2. 파싱 및 무결성 검증 (Parsing & Validation)
- **플로우 참고:** `claude-json-build.md`, `claude-gemini-flow.md`, `claude-validation-harness.md` 기반.
- **검증 규칙 (공식):** [`kics-json-validation-rules.md`](kics-json-validation-rules.md) — rules 1-8 + R4/R7; code in `src/solvency/validation/kics_json_rules.py`.
- **[필수 게이트]:** `python scripts/validate_kics_disclosure.py` 실행 후 **RED=0** (또는 `TODO.md`에 문서화된 예외만) 확인 전 다음 단계(JSON swap, template sync, deploy) 진행 금지. 예상치 못한 RED는 파싱 오류 검토 필수.
- **추출 대상 항목:** 가(지급여력금액), 나(지급여력기준금액), 다(지급여력비율) 및 하위 항목 전체.
- **[신규 필수 사항]:** `생명장기손해보험위험액`의 하위 항목 (사망/장수/장해질병/장기재물기타/해지/사업비위험) 파싱 로직을 추가할 것 (분기/반기 공시에 따라 변동 가능성 유의).
- **[Image-only PDF 룰]:** `claude-gemini-flow.md`에 명시된 대로 텍스트 추출이 불가능한 PDF를 마주치면, 억지로 OCR 스크립트를 짜지 말고 사용자에게 수동 파싱을 요청할 것.
- **[무결성 룰 (Cross-Quarter)]:** 생성된 JSON을 전 분기 데이터와 비교할 것. '기타요구자본' 및 그 이하 항목을 제외하고, **전 분기에 값이 있던 항목이 이번 분기에 누락되었다면 파싱 실패로 간주**하고 원인을 분석할 것 (조용히 넘어가기 금지).


### Split-table parsing (Samsung Life / Shinhan Life — 2026-05-25)

Some life insurers split solvency **amount** (item1) and **SCR** (item14) across sections:

1. **[지급여력비율총괄] / ※ … 총괄** — two-column label table (경/과/전 + metric name). Parser: extract_kics_summary_overview_rows. Strip parenthetical suffixes like (A), (B), (A/B).
2. **[경과조치적용전지급여력비율세부]** — detail rows for items 2–23. May appear as ## ※ … (no brackets) or split across continued pages (나.지급여력기준금액 on a later table).
3. **Quarter headers** — match 2024년2/4분기 via make_quarter_column_picker (N/4분기 pattern).

Label hygiene (kics_disclosure_parser.py):
- Item **22** (법인세조정액): store **positive magnitude** (parentheses in MD); rule5 = item15 - item22 + item23.
- **비율 vs amount**: labels_compatible rejects matching 기본자본비율 to 기본자본.
- Shinhan OCR variants: middle-dot ∙, 보험→보X위, 손액보험→손해보험.
- **fill_period**: _supplement_core_baseline adds missing item 1–28 templates (e.g. item10 비지배지분 when prior quarter omitted it).

When RED samples show obvious MD/label mismatch for a company, **reparse proactively** — do not wait for user callout.

## 3. 마무리
- 모든 검증(`lint + unit + golden + validate + pdf`) 통과 후 Github Repository `insurequant`에 push 완료하기 전에는 세션을 종료하지 말 것.
