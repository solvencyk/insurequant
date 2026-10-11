---
from: orchestrator
to: validation
created: 20261012T0300Z
status: open
route: gate-change
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 질문(2026-10-12): 「pre push gate 가 왜 30분 남짓 걸리는지 체크해봤어?」 오케스트레이터 실측(읽기만):

- 풀 훅 26분 42초 중 pytest 24분 43초(772건). 그중 `tests/test_rule_coverage_manifest.py::test_full_gate_coverage_matches_manifest` **한 건이 1,120초(18.7분)** — `FULL_COVERAGE_SWEEP=1`(훅 모드)에서 48칸을 하나씩 변이시켜 `validate_kics_disclosure.main()` 을 칸마다 한 번씩 돌리는 테스트다(주석: 게이트 1회 ≈4초, 전수 ≈4분이라고 가정했다). 지금은 게이트 1회가 **약 23초**(cProfile 하에서 40.7초).
- `scripts/validate_kics_disclosure.py` 를 cProfile 로 재면 40.7초 중 **약 23초가 pymupdf `get_text`(2,372쪽 PDF 텍스트 추출)** 이고 호출 경로는 `_exemption_provenance_findings`(L3845, 누적 21.0초) → `_verify_absent_markers`(L3749, 21.3초)·`_verify_present_rows`(L3727)·`_row_anchor_check`(L3672, 10.9초) 와 `_marker_grade_census`(L4138, 9.6초), `_scan_breakdown_presence`(L539, 3.9초). 즉 **등재 예외의 원문 재검산이 게이트를 돌 때마다 같은 PDF 를 처음부터 다시 연다.** 변이시험은 K-ICS 마스터 값만 바꾸고 PDF·등재부는 그대로인데 49번 반복한다.
- 훅 구성 시간 대략: 데이터계약 ≈44초, K-ICS 게이트 ≈23~40초, 도메인 게이트 수 분, pytest 24분(그 안에 위 한 건 18.7분), 나머지 시험 ≈6분.

### 해 줄 것 (게이트 **판정은 바뀌면 안 된다**, 속도만)
1. **원문 텍스트 읽기를 프로세스 내 캐시**한다: PDF 열기·`page.get_text()`·`get_text_words()` 결과를 (경로, 파일 크기, mtime_ns) 키로 한 번만 읽도록 공용 헬퍼(`functools.lru_cache` 또는 모듈 dict)에 모은다. 캐시 키에 파일 상태를 넣어 PDF 가 바뀌면 자동 무효화. 캐시는 **텍스트만**(결과·판정은 캐시하지 않는다 — `_marker_grade_census`·`_row_anchor_check` 는 행에 의존하므로 매번 계산). 메모리 폭주 방지(페이지 문자열 합계 상한 또는 LRU 크기) 확인.
2. **전후 측정**: 게이트 1회(첫 실행·두 번째 실행)와 `FULL_COVERAGE_SWEEP=1` 로 `tests/test_rule_coverage_manifest.py` 전체 소요를 전/후로 보고(기대: 두 번째 이후 게이트 ≈3~6초, 테스트 18.7분 → 약 3~4분). 판정 불변 증명: 변경 전후 게이트 출력(리포트 findings 전체) 바이트 비교(타임스탬프 제외) + `tests/test_kics_rules_golden.py`·`tests/test_rule_coverage_manifest.py`·`tests/test_data_contract_selftest.py` 통과 + 변이시험(캐시를 깨뜨려 stale 을 일부러 만들었을 때 잡히는지: 같은 경로 PDF 를 다른 내용으로 바꾼 임시 파일로 키가 무효화되는지).
3. **추가 후보(측정 후 효과가 큰 것만)**: `_scan_breakdown_presence`·`_marker_grade_census` 의 파일 읽기, `validate_data_contract.py`(≈44초)·`validate_master_tables.py` 의 같은 패턴(PDF/MD 반복 읽기)이 있는지 프로파일하고 같은 캐시를 쓰게 한다. 기존 `scripts/_disclosure_pdf_paths.py` 규약은 그대로.
4. `scripts/prepush_check.py` 의 주석(「~4분」「~18분」 등 소요 숫자)을 실측으로 고친다. 훅 배선·게이트 순서·시험 목록은 바꾸지 않는다.

### 규칙
- 마스터 JSON·등재부·골든 값 수정 금지(속도만). 게이트 판정·예외 로직 변경 금지. `validate_master_tables.py` 는 `--no-build`. 서브에이전트 금지, docling 금지. 커밋은 자기 파일만(명시 경로, `git add -A` 금지, `data/_derived/qoq_warn.json` 제외), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. push 금지. 파이썬은 풀패스·스크립트 파일만. 이 공유 티켓은 고치지 않는다.
- 다른 에이전트가 마스터를 쓰는 중이라 게이트 출력 비교는 **같은 마스터 상태에서 전/후 연속 실행**으로 한다(백업 바이트 오버레이 방식 참고: `data/_derived/bspl_apply_20261011/item4_reinsurers_lina6/gate_overlay.py`).

### 보고
- 전/후 소요(게이트 1회 첫·재실행, 매니페스트 테스트, 추정 훅 총 시간), 판정 불변 증명, 변경 파일·커밋 해시를 2~4줄로.

## 답변 (recipient 작성 — 처리 후)
