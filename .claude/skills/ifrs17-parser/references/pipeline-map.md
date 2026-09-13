# IFRS17 lane — pipeline map, file map, schemas, run/verify

Operational reference. For *domain* depth (label variants, table-form taxonomy, slice rules) see the SOT
`docs/domains/claude-agent-ifrs17.md`. This file is the current code/data wiring (verified 2026-06-16).

## Table of contents
- [Sources (raw)](#sources-raw)
- [Extractors](#extractors-srcifrs17)
- [Batch drivers + masters/viz builders](#batch-drivers--builders-scripts)
- [Outputs](#outputs)
- [Schemas](#schemas)
- [Run / verify recipes](#run--verify-recipes)

## Sources (raw)
`data/dart/FY{2023,2024,2025}_Q4/raw/KR####_<canonical>_<rcept14>/*.xml` — DART filing XML (HTML-table
format: `<TABLE><TR><TD>`, numbers comma-grouped, negatives in parentheses, labels often 전각-spaced).
- A filing usually carries **별도(separate) + 연결(consolidated)** statements. The masters are built on the
  **별도** statements for life insurers; prefer 별도 when both exist and record which you used.
- ⚠️ On `fix/csm-…` most FY2023/FY2024 raw is **git-purged**; only **AIA (KR0080) FY2024** + **all FY2025_Q4**
  raw survive on disk. `data/dart/extracted/*.json` are committed and intact.

## Extractors (`src/ifrs17/`)
Semantic scoring, **no per-company regex** (see SOT §3.2). One module per table kind:

| module | table kind | note |
|---|---|---|
| `csm_extractor.py` | CSM amort schedule / `csm` | Form A (year=col), A_rows (year=row), B (snapshot), unknown |
| `measurement_extractor.py` | `measurement` | §14(4) 측정요소 rollforward — the CSM-change body |
| `insurance_pl_extractor.py` | `insurance_pl` | §14(5) 보험손익 상세 |
| `reinsurance_extractor.py` | `reinsurance` | §14(3)(4) 출재 (장기 only) |
| `bs_snapshot_extractor.py` | `bs_snapshot` | §14(1) 자산부채 현황 |
| `sensitivity_extractor.py` | `sensitivity` | 가정민감도 / 보험위험의 민감도 분석 (DART note) |
| `liability_extractor.py` | `liability` | §14(3) multi-index 부채 변동 (skim/structural) |
| `kics_sensitivity_extractor.py` | `kics_sensitivity` | K-ICS rate-sensitivity (lane-adjacent; KR####_FY####_Q#_kics_sensitivity.json) |
| `scoring.py` | — | shared table-scoring keywords (`data/ifrs17/table_scoring_keywords.yaml`) |
| `row_normalizer.py`, `universe.py`, `opendart_client.py`, `config.py` | — | row alias / universe+slice policy / DART REST / `.env` |

## Batch drivers + builders (`scripts/`)
- **Batch (raw → extracted):** `ifrs17_batch_{measurement,insurance_pl,reinsurance,bs_snapshot,sensitivity,
  all,historical,kics_sensitivity}.py`; `ifrs17_batch_sensitivity_fy2025.py` (the FY2025 refresh — groups raw
  by canonical, merges multi-dir audit filings, keys by max rcept).
- **Masters (extracted → master JSON):** `build_csm_waterfall_master.py`, `build_pl_breakdown.py`,
  `build_nb_csm_multiple.py`, `build_net_income_breakdown.py`. `build_root_masters.py` = the **join point**,
  run once **after both lanes have loaded**.
- **Viz (→ data/dart/viz panels):** `viz_build_ifrs17_panels.py` (bs_snapshot, csm_amort_schedule,
  insurance_pl_breakdown, sensitivity_heatmap), `viz_build_csm_waterfall.py`, `viz_build_ifrs17_kpis.py`.
- ⚠️ `build_csm_waterfall_master.py` and `build_pl_breakdown.py` **discover from `data/dart/FY*/raw/`** →
  **destructive on this branch** (collapses masters). See quirks-and-traps.md §destructive-rebuild.

## Outputs
- `data/dart/extracted/<canonical>_<rcept>_<kind>.json` (+ `_mvp` filtered variants, + `_*_summary` /
  `_batch_*_summary` index files). Counts (2026-06): csm 29, sensitivity 29, measurement/insurance_pl 28,
  reinsurance/bs_snapshot 23, liability 5.
- **Masters (committed, tracked):** root `CSM_waterfall.json`, `PL_breakdown.json`, `NB_CSM_multiple.json`.
- **Viz panels (committed):** `data/dart/viz/{bs_snapshot, csm_amort_schedule, csm_waterfall*, csm_bubble*,
  insurance_pl_breakdown, net_income_breakdown, pl_breakdown_master, sensitivity_heatmap, downstream_kpis,
  earnings_quadrant, …}.json`. Consumed by `IFRS17.html` / `index.html`.

## Schemas

**Extracted block** (one table candidate; files are a list of these):
`caption, block_type, slice_label, slice_policy, mvp_candidate, line_no, score, reasons, header (list of
header rows), rows (list of cell-lists), footnotes, _source_xml`.

**`sensitivity_heatmap.json`** — `{period, companies: [ {company, rcept_no, status, caption, table_kind,
unit ("억원"), unit_detected, unit_source, header, scenarios: [ {risk, shock, csm_delta, pl_impact} ] } ]}`.
- `status` ∈ ok / partial / empty. `csm_delta = null` = CSM column not disclosed (PL-only filing).
- **build_panel best-status dedup:** per company keep `max((STATUS_RANK[status] {ok:3,partial:2,empty:1},
  rcept))` across all its `*_sensitivity.json` files → a FY2025 extract (rcept 2026…) supersedes FY2024
  (rcept 2025…) **only when its status ≥**. Files without a 14-digit rcept (the kics `*_kics_sensitivity.json`)
  are skipped so they never enter an ifrs17 panel.

**PL master** (`pl_breakdown_master.json` ≡ root `PL_breakdown.json`) — flat list of
`{원보험사코드, 원수사명, 티커, 생손보여부, 항목번호, 항목명, 공시분기, 값[, 값_당분기]}`. 31 항목 per
(company, quarter):
```
1 보험손익  2 생명장기 손익  3 생명장기 원수손익  4 원수 CSM상각  5 원수 위험조정 변동  6 원수 예실차
7 기타 생명장기 원수손익  8 생명장기 재보험손익  9 재보험 CSM상각  10 재보험 위험조정 변동  11 재보험 예실차
12 기타 생명장기 재보험손익  13 자동차손익  14 일반손익  15 기타영업수익  16 기타사업비용  17 투자손익
18 투자이익  19 보험금융손익  20 영업이익  21 영업외손익  22 세전이익  23 법인세  24 당기순이익
25 기타포괄손익  26 FVOCI 채무증권 평가손익  27 보험계약금융손익(OCI)  28 위험회피 파생상품 평가손익
29 FVOCI 지분증권 평가손익  30 재보험금융손익(OCI)  31 총포괄손익
```
값 unit = **백만원**. **Closure identities** (use to detect mis-parses):
`item1 = item2 − item16` · `item17 = item18 + item19` · `item20(영업이익) = item1 + item17` ·
`item24 + item25 = item31`.
Surgical cell fix without a rebuild: `_GOLD_CELL_OVERRIDE[(code, quarter)] = {item: value}` in
`build_pl_breakdown.py` (FS-API-absent / two-line-investment companies, e.g. 메트라이프 KR0095, 하나생명 KR0097).

**Items 25-31 (총포괄손익 extension, 2026-08-28)** — sourced ONLY from `data/dart/_fs_api_cache/
*_OFS.json`'s `sj_div=='CIS'` rows via `fetch_dart_fs.py::ACCT_OCI` (account_id-keyed, never
account_nm — a company can rename the same tag's label across filing years, e.g. 삼성생명
`기타포괄손익`→`법인세비용차감후기타포괄손익`; account_id stays `ifrs-full_OtherComprehensiveIncome`
throughout). Never comes from the HTML fallback (`pl_breakdown/tier1.py`) or Tier-2 LOB notes —
a filing with no FS-API CIS section (audit-only non-listed insurers, ~12 companies) has these 7
items `null`, same as any other missing cell (no SKIP-on-missing). `값_당분기` for these items is
NOT set by `build_pl_breakdown.py` itself — it comes for free from `build_root_masters.build_pl()`,
which derives 당분기 generically for every item via YTD-differencing (no PL item range hardcoded
there). Two gate rules cross-check this extension in `validate_master_tables.py`: `PL_EQS`'s 8th
equation (`총포괄손익 = 당기순이익+기타포괄손익`, folds into the existing `pl_bridge` SUMMARY field,
RED-eligible — census-verified exact-0 residual) and `_check_pl_oci_vs_bs_aoci()` (item25 값_당분기
vs `IFRS17_BS.json` item4 QoQ delta, YELLOW-only — real accounting noise from reclassification/
capital transactions, worst at 4Q). Both registered in `tests/test_identity_registry.py::REGISTRY`
(`pl_bridge`, `pl_oci_vs_bs_aoci`). See `inbox/parser/20260828T0113Z__owner__MULTI__
oci_extension_pl_breakdown.md` for the full census.

## Run / verify recipes
PY = `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`

- **Unit + golden gate:** `PY -m pytest tests/unit/` (extractor units + E2E XML fixtures).
- **Refresh sensitivity (one company, surgical):** generate just that company's FY2025 extracted
  `<canonical>_<rcept>_sensitivity.json` (mirror `ifrs17_batch_sensitivity_fy2025.py` per-company logic),
  then `PY scripts/viz_build_ifrs17_panels.py`. best-status dedup flips only that company; diff the heatmap
  per-company to confirm exactly one changed and 3 sibling panels stay byte-identical.
- **Full FY2025 sensitivity batch:** `PY scripts/ifrs17_batch_sensitivity_fy2025.py` then the panel rebuild.
  ⚠️ FY2025 product-row / 원수·출재·순액 sub-row layouts (농협생명, 케이디비, …) currently emit garbage via the
  band/generic path — verify per company before shipping; keep mis-parsing companies on FY2024 (phase-2 work).
- **After any master JSON change:** `PY scripts/build_master_xlsx.py` to regenerate
  `insurequant_master_tables.xlsx` (review-loop sync).
