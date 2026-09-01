---
from: validation
to: parser
created: 20260901T0430Z
status: open
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

## 답변 (recipient 작성 — 처리 후)
