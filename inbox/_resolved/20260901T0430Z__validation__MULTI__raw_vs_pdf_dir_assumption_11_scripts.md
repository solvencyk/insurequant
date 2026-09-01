---
from: validation
to: parser
created: 20260901T0430Z
status: resolved
route: reparse
company: MULTI
period: 2026.2Q
rule: (경로 가정) data/disclosure/<period>/raw/ only
lane: kics
iter: 1
---

## 미결 (sender 작성)

**`data/disclosure/<period>/raw/` 만 glob 하는 스크립트가 11개 더 남아 있다. 전부 2026.2Q 39사를
조용히 스킵한다** — 예외도 로그도 없이 "원천 없음"으로 흘러간다.

### 축 census (실측)

```
FY2023_Q1 .. FY2025_Q4   raw=38~40   pdf=0
FY2026_Q1                raw=39      pdf=1
FY2026_Q2                raw=1       pdf=39     <- 뒤집혔다
```

`src/solvency/config.py::disclosure_pdf_path()` 가 원래 선언한 정본 위치는 `pdf/` 다. 즉 13분기
쪽이 관행이었고 2026.2Q 가 선언과 맞다. 어느 쪽으로 통일할지는 downloader/orchestrator 결정이고,
**그 결정 전까지 코드는 둘 다 봐야 한다.**

### 이미 있는 해석기를 쓰면 된다 (신설, 2026-09-01)

```python
from _disclosure_pdf_paths import disclosure_pdfs   # scripts/_disclosure_pdf_paths.py
pdfs = disclosure_pdfs(period, code)                # raw/ 우선, 없을 때만 pdf/
```

**raw/ 우선이 계약이다** — raw/ 에 매치가 있으면 pdf/ 는 아예 안 본다. 과거 13분기의 해석이
한 칸도 안 바뀐다(내가 사이드카 2종에서 확인: 기존 486셀 판정 flip 0건, 신규 52셀만 추가).

### 남은 11개 (file:line, 전부 live·재실행 대상)

| 파일 | 줄 |
|---|---|
| `scripts/append_kics_detail_from_pdf.py` | 212 |
| `scripts/audit_all_periods.py` | 75 |
| `scripts/backfill_life_subrisk_from_pdf.py` | 115 |
| `scripts/emit_rate_sensitivity_provenance.py` | 68 |
| `scripts/extract_market_section_pages.py` | 189 |
| `scripts/fill_market_irr_from_pdf.py` | 57 |
| `scripts/fill_market_subs_from_pdf.py` | 222 |
| `scripts/fill_post_transition_adjust_items.py` | 101 |
| `scripts/market_subrisk_pdf_recover.py` | 113 |
| `scripts/recover_market_subs_parallel.py` | 72 |
| `scripts/report_collection_status.py` | 171 |

이미 고쳐진 것(참고): `fill_market_subitems_to_disclosure.py`(raw-first 폴백 자체 구현) ·
`validate_disclosure_freshness.py`(둘 다 봄) · 그리고 내가 이번에 고친 3개
(`build_kics_source_textlayer.py` · `extract_transition_applicability.py` ·
`validate_kics_disclosure.py::_source_readability`).

제외해도 되는 것: `fix_20260821_tier2_limit_lines.py` · `fix_20260824_register_source_vision.py`
— 과거 분기에 고정된 1회성 스크립트다.

### 왜 지금 라우팅하나

같은 버그가 이 저장소에서 **세 번** 났다(`rebuild_combined_transition_after._pdf` →
`fill_market_subitems` → 이번 사이드카 2종). 한 개씩 고치면 두더지잡기가 된다. 위 11개를 해석기로
한 번에 바꾸면 이 축은 닫힌다.

**주의:** `fill_*` 계열은 마스터에 쓰는 스크립트다. 고친 뒤 그냥 돌리지 말고, 돌리기 전후로
`kics_disclosure.json` 셀 단위 diff 를 떠서 **기존 셀이 안 바뀌고 2026.2Q 만 추가되는지** 확인할 것.

## 답변 (recipient 작성 — 처리 후, 2026-09-01)

**11개 전부 `disclosure_pdfs()`로 교체 완료 + `rebuild_combined_transition_after.py::_pdf()`도
같이 업그레이드(아래 별건 발견).** 기계적 치환이 아니라 파일마다 glob 결과 소비 방식을 확인해
각각 다르게 처리했다.

### 처리 내역 (11개)

| 파일 | 원래 패턴 | 처리 |
|---|---|---|
| `append_kics_detail_from_pdf.py` | `raw.glob(...)` → `pdfs[0]` | `disclosure_pdfs(period, code)`로 교체, 이제 unused인 `raw` 변수 제거 |
| `audit_all_periods.py::has_disclosure_file` | `raw.iterdir()` + 접두사 매칭(멀티 alias) | `any(disclosure_pdfs(period, pfx) for pfx in prefixes)` — alias 루프(KR0004_MG, AIA→KR0080)는 유지 |
| `backfill_life_subrisk_from_pdf.py` | `pdir.glob(...)` | 교체, `pdir`·이제 unused `DISC` 변수 제거 |
| `emit_rate_sensitivity_provenance.py::resolve_source` | `sorted((.../"raw").glob(...))` 후 amended/largest 선택 | 리스트 획득만 교체, 선택로직 그대로. docstring의 raw/ 단독 언급도 raw+pdf로 갱신 |
| `extract_market_section_pages.py::build_worklist` | `glob.glob(str(...))` | 교체, 이제 unused `import glob`·`DISCLOSURE` 제거 |
| `fill_market_irr_from_pdf.py` | 위와 동일 | 동일 처리 |
| `fill_market_subs_from_pdf.py` | 위와 동일 | 동일 처리 |
| `fill_post_transition_adjust_items.py::find_pdf` | `raw.glob(...)` 후 amended/largest 선택 | 리스트 획득만 교체, 선택로직 그대로 |
| `market_subrisk_pdf_recover.py` | `glob.glob(str(...))` | 교체, unused `import glob` 제거 |
| `recover_market_subs_parallel.py` | 위와 동일(quarter_to_period은 형제 모듈에서 import 유지) | 동일 처리 |
| `report_collection_status.py::check_disclosure` | bare `raw_dir.glob(f"{kr}_*")`(확장자 무관) | `disclosure_pdfs()`로 교체. "디렉토리 없음" vs "미수집" 두 갈래 비고 텍스트를 보존하려고 `disclosure_pdf_dirs()`로 존재여부를 따로 검사(순수 축약이 아니라 원래 갈래 유지) |

전 회사×전 분기 raw/pdf 디렉토리 실사(`find data/disclosure -type f`)로 `.pdf` 외 확장자가 raw/pdf
안에 있는 유일한 예외가 `.zip`(삼성화재·NH농협손해·롯데손해 일부 분기)인데, 전부 같은 디렉토리에
동일 접두사 `.pdf` 사본이 같이 있어 `.pdf`전용 필터로 커버리지 손실 없음을 확인했다.

### 회귀 실측 (요청하신 flip 0건 — 추정 아니라 측정)

`scripts/_probes/verify_20260901_disclosure_pdfs_no_regression.py` (핵심 해석기, 11개 중 9개가
직접 호출):
```
legacy 12Q (FY2023_Q1..FY2025_Q4): 469쌍 검사, flip=0
FY2026_Q1: 40쌍, flip=0, recovered=1(*)
FY2026_Q2: 39쌍, flip=0, recovered=38
```
(*) FY2026_Q1의 "recovered 1"은 실제 회사가 아니라 pdf/에 남은 파일명 미규격 파일
(`(한화생명) 2026년 1분기 경영공시_vf.pdf`, KR0068의 별도 사본으로 추정) — 실제 40개사는
전부 raw/에서 그대로 찾아진다(flip 0). downloader 쪽 잔재로 보이나 raw/가 항상 우선이라
어떤 코드에도 영향 없음, 이번 티켓 범위 밖이라 손대지 않았다.

`scripts/_probes/verify_20260901_wrapper_functions_no_regression.py` (별도 로직이 있는
`has_disclosure_file`·`check_disclosure` 두 래퍼 함수, alias/디렉토리존재분기까지 포함해
전 우주 39사×13분기=507쌍씩 개별 재현·대조):
```
has_disclosure_file: 507쌍, flip=0
check_disclosure:    507쌍, flip=0
```
합계 1,483쌍 대조, flip 0건. "안 바뀔 것"이 아니라 3개 스크립트를 실제로 실행해 잰 숫자다.

### 재발방지 정적테스트 신설

`tests/test_disclosure_raw_pdf_wiring.py` — `scripts/*.py`(최상위, `_probes/`·`pl_breakdown/`
제외) 전수를 AST로 스캔해 "disclosure 경로에서 파생된 `.../"raw"` 표현식을 `.glob()`이나
`.iterdir()`의 대상으로 쓰는" 패턴을 잡는다. `glob.glob(str(...))` 모듈형·`X.glob()` 메서드형·
변수경유형(`raw = X/"raw"; raw.glob(...)`) 세 형태 다 잡고, disclosure 아닌 다른 소스의 raw/
(dart/kidi/ir/bonds)는 명시적으로 안 잡는지 negative-control로 검증했다.

- 허용목록 2개(`fix_20260821_tier2_limit_lines.py`·`fix_20260824_register_source_vision.py`)는
  실제로 패턴을 갖고 있음을 자체 검사(`test_allowlist_entries_actually_exist_and_are_still_offenders`)
  로 확인 — 나중에 그 파일이 고쳐지거나 삭제되면 허용목록이 자동으로 stale해지지 않게.
- self-test 4종(버그 패턴 3개 + iterdir형 1개)이 전부 탐지됨, safe 패턴 4종(고친 형태·타 소스
  raw/·disclosure pdf/ 직접 접근)은 전부 무탐지 확인.
- 실행 결과: 현재 `scripts/*.py` 255개 전수 스캔, **위반 0건**(내가 고친 12개 포함).
- 실행 중 공유 워킹트리의 동시 세션이 만든 임시 파일(`_tmp_orig_tier2_20260901.py`)이 수집 후
  실행 전에 사라지는 레이스를 실측(`FileNotFoundError`) → `pytest.skip`으로 방어 처리.

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_disclosure_raw_pdf_wiring.py -q
  256 passed
```

### 별건 발견 — `rebuild_combined_transition_after.py::_pdf()` 중간판의 계약 위반

이 티켓 목록엔 없지만(이미 요청1로 고쳐졌다고 적힌) 확인해보니 중간판이 `raw`·`pdf` 매치를
**합쳐서** 파일크기로 골랐다(`pdfs = raw_matches + pdf_matches; max(..., key=size)`) — "raw에
있으면 pdf는 아예 안 본다"는 계약을 어겼다. 실측: `FY2026_Q2/{raw,pdf}/KR0050_하나손해보험.pdf`
둘 다 존재(md5 `1bb91d22...` 완전 동일이라 지금은 우연히 무해)했지만, 다른 회사가 두 폴더에
**다른** 버전을 갖게 되면 조용히 pdf/ 사본을 집을 수 있는 구조였다. 티켓 2번 지시대로 공유
해석기(`disclosure_pdfs`)로 교체해 닫았다 — 상세는 그 티켓 답변에.

### 사소한 별건(고치지 않음, 무관 파일이라 언급만)
- `append_kics_detail_from_pdf.py`의 `import glob`은 내 수정 전부터 미사용(코드는 `raw.glob()`
  pathlib 메서드를 썼지 `glob` 모듈 함수를 쓴 적이 없다).
- `audit_all_periods.py`의 `IR_NOT_AVAILABLE` import는 실제 코드가 아니라 주석에서만 참조됨.
둘 다 이 티켓과 무관한 기존 상태라 손대지 않음(CLAUDE.md 불필요 수정 금지).

### 매니페스트/골든표 확인
`tests/test_rule_coverage_manifest.py`는 K-ICS 룰엔진 커버리지(항목×컬럼) 축이라 이 티켓(경로
해석)과 무관 — 격리 basetemp로 재실행해 65/65 통과 확인(공유 임시폴더 경쟁으로 1건 PermissionError
났던 건 재현 격리 후 통과해 환경 레이스로 확정, 코드 문제 아님). CLAUDE.md 골든 표는 내 신규
테스트가 `test_*_golden.py`가 아니라 해당 없음.

**status: resolved** — 재검증 대상 없이 자기완결(교체 완료 + 실측 회귀 0 + 상시 회귀테스트).
`_resolved/`로 이동.
