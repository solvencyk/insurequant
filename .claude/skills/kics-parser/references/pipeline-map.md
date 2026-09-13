# K-ICS lane — pipeline map, file map, schemas, gate, run/verify

Operational reference. For *rule* depth (formulas, R4/R7, MARKET_M) see `docs/agents/kics-json-validation-rules.md`
+ `docs/agents/kics-market-risk-decomposition.md`; the code `src/solvency/validation/kics_json_rules.py` is final.
This file is the current code/data wiring (verified 2026-06-16).

## Table of contents
- [Sources (raw) + MD](#sources-raw--md)
- [Pipeline order + extractors](#pipeline-order--extractors-scripts)
- [Item numbering 1-46](#item-numbering-1-46)
- [File map + schemas](#file-map--schemas)
- [The validation gate](#the-validation-gate)
- [Run / verify recipes](#run--verify-recipes)

## Sources (raw) + MD
`data/disclosure/<PERIOD>/raw/KR####_<원수사명>.pdf` — the insurer's quarterly **정기경영공시** PDF
(`PERIOD` = `FY2023_Q1` … `FY2026_Q1`). `data/disclosure/<PERIOD>/parsed/*.md` mirrors the docling output; the
fill scripts read from `md_inbox/<PERIOD>/KR####_<name>.md` (code = `stem.split("_",1)[0]`). raw is gitignored
but **on disk** (purge-independent). Docling MD = markdown tables; numbers comma-grouped, negatives as **△**.

## Pipeline order + extractors (`scripts/`)
```
raw PDF ──docling──▶ md_inbox MD ──▶ fill_period (1-28) ──▶ fill_subitems (29-35) ──▶ fill_market_subitems (36-40 +41-46)
  run_harness.py        │                                                                       │
  --stage parse         │                                              fill_market_irr_from_pdf (41-46 recovery, fitz)
  (venv python,         │                                                                       │
   ~100s/PDF)           └──────────────────── validate_kics_disclosure.py (GATE) ◀──────────────┘
```
| script | items | note |
|---|---|---|
| `run_harness.py --stage parse` | — (PDF→MD) | docling; keyword-localizes 지급여력 pages, parses hit-page ±window only. Writes `parsed/*.md` + `md_inbox/`. Needs **venv** python. |
| `fill_period_to_disclosure.py` | **1-28** core | UPSERT from MD. Side effects: `STALE_DELETES`, `_reconcile_item4_from_components`, pops prior-quarter `값_적용후`. Baseline = prior quarter, else best available. |
| `fill_subitems_to_disclosure.py` | **29-35** 생명장기 subs | parent-gate (item17≤0 ⇒ drop) + `_is_life_catastrophe_table` (item35 only from life catastrophe tables). |
| `fill_market_subitems_to_disclosure.py` | **36-40** 시장 (+ 41-46) | 36-40 from MD; pulls IRR 41-46 from raw via fitz. M-matrix lives here (`M`). |
| `fill_market_irr_from_pdf.py` | **41-46** | recovery pass from raw PDF, **gated vs item36** (stores only GREEN-by-construction). |
| `extract_market_section_pages.py` | — (Phase-0 localizer) | finds 시장위험 pages → `artifacts/kics_validation/market_pages/`. **pdfplumber → fitz fallback** on EOF. |
| `validate_kics_disclosure.py` | — (GATE) | `run_validation` + 4 structural gates (below). |
| `build_master_xlsx.py` | — | rebuild `insurequant_master_tables.xlsx` after any master edit. |

Flat integer `항목번호` key (no `17.1` sub-numbering) so downstream keying by 항목번호 keeps working.

## Item numbering 1-46
1 가.지급여력금액 · 2 기본자본 · 3 보완자본 · 4 순자산(건전성BS) · 5 보통주 · 6 보통주외 자본증권 · 7 이익잉여금 ·
8 자본조정 · 9 기타포괄손익누계 · 10 비지배지분(opt,0) · 11 조정준비금(opt,0) · 12 불인정항목 · 13 보완자본 재분류 ·
**14 나.지급여력기준금액(SCR)** · 15 기본요구자본 · 16 분산효과 · **17 생명장기손해보험위험액**(parent of 29-35) ·
18 일반손해보험위험액 · **19 시장위험액**(parent of 36-40) · 20 신용위험액 · 21 운영위험액 · 22 법인세조정액(store +magnitude) ·
23 기타요구자본(opt,0) · 24-26 종속/관계회사 환산·대응치 · **27 다.지급여력비율(=1/14×100, %)** · 28 기본자본비율(=2/14×100, %) ·
**29-35** 생명장기 subs = 사망·장수·장해질병·장기재물기타·해지·사업비·대재해(1-1..1-7) ·
**36-40** 시장 subs = 금리·주식·부동산·외환·자산집중(3-1..3-5) ·
**41-46** 금리위험 순자산가치 = 충격전·평균회귀·금리상승·금리하락·금리평탄·금리경사(3-1-0..3-1-5).

## File map + schemas
**`kics_disclosure.json`** (root, long-format, unit **억원**) — key order is load-bearing (`fill_period._fields()`
reads positionally `k[0..7]`): `원보험사코드`·`원수사명`·`티커`·`생손보여부`·`항목번호`·`항목명`·`공시분기`(`YYYY.nQ`)·`값` +
optional `값_적용후` (경과조치 적용후; mostly on 1-28). `항목명` is descriptive only — validator + consumers should
key by `항목번호` (note: item1/item27 carry two label-string variants — long form vs short '지급여력금액'/'지급여력비율').

**`kics_rate_sensitivity.json`** (root, wide-format) — `원보험사코드`·`원수사명`·`티커`·`생손보여부`·`공시분기`·
`경과조치여부`(적용전|적용후)·`measure구분`(지급여력비율|지급여력금액|지급여력기준금액)·shocks `-100bp`·`-50bp`·`base`·
`+50bp`·`+100bp` (floats; 비율 %, 금액 억원). One row per (co × quarter × 경과조치 × measure). **Non-appliers**: 적용후
= 적용전 (duplicate); confirm via MD "경과조치 전·후 동일" / "해당사항 없음" before duplicating.

**`artifacts/kics_validation/`** — `report_<UTC>.json` + `report_latest.json` (every gate run); `market_pages/`
localized sections + `market_pages_nonok.json` (localizer-failure worklist).

## The validation gate
`run_validation` rules (per (원보험사코드, 공시분기) bucket): **1** item1=2+3 · **2** item4=Σ(5-11) · **3** SKIP(always) ·
**4** item15=√(Vᵀ·R4·V)+item21, V=[17,18,19,20] · **5** item14=15−22+23 · **6** item16=Σ(17-21)−15 ·
**7** item27=1/14×100 · **8** item28=2/14×100 · **8_post** uses item2 값_적용후 · **9** item2후≥전 · **10** item14전≥후 ·
**8_life** item17=√(Sᵀ·R7·S), S=[29-35] — **SKIP** on missing · **19_market** item19=√(Vᵀ·MARKET_M·V), V=[36-40],
partial OK(missing→0) — **SKIP** if item19 or all 36-40 missing · **36_irr** item36=√(max(R상승,R하락)²+max(R평탄,R경사)²)
+R평균회귀, R=base(41)−scenario — **SKIP** if item36 or any 41-46 missing.
Tolerance default **2.0**; 8_life/19_market/36_irr use `max(tol, 0.05·|expected|)`; image-OCR insurers (KR0010, KR0079)
tol **10.0**. Status: GREEN |diff|<0.5, YELLOW ≤tol, RED >tol or missing input.

**4 structural gates beyond rule findings (force exit 2):**
- `_coverage_census` — "regular filers" (codes in ≥ max(2, n_q//2) quarters) missing from a quarter → RED. Catches
  the wholesale-under-parse blindspot (2026.1Q held 1 of ~35 filers, rules emitted nothing → false RED=0).
- `_parent_zero_child_nonzero` — parent {17→29-35, 19→36-40} present & |v|<1 but a child |val|≥1 = cell-shift
  misparse (structurally impossible). Real case: 서울보증 25.4Q item17=0 / item35=5212 (일반손해 대재해 leak).
- `_scan_breakdown_presence` — for item19-disclosed-but-36-40-absent, reads the MD; ≥3 distinct 시장 sub-risk rows
  ⇒ parser gap (RED), else cadence (legit SKIP). Strips numeric prefixes to dodge 경과조치 compound-string false-pos.
- `_market_tooling_fail` (advisory, non-blocking) — localizer ERR/NO_SIGNAL/TIMEOUT worklist.

**Gate contract (CLAUDE.md):** RED must be **0**, OR every RED is a documented exception in `TODO.md` (company,
quarter, rule, reason). Permanent skip cohorts in TODO.md: **KICS-SUB** (KR0029, KR0150, KR1098 …), image-OCR
**KICS-IMG** (KR0010, KR0079). Exit 0 only if red=0 AND census_red=0 AND parent-child empty.

## Run / verify recipes
PY = `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` (docling lives in the venv, not system python).
Diagnostics go in `scripts/_probes/*.py` (never inline multi-line `python -c` — it hangs Windows shells).

```
# parse one quarter (docling) — optional company filter; raw may be under raw/ not pdf/
PY scripts/run_harness.py --stage parse --period FY2025_Q4 --pdf-root data/disclosure/FY2025_Q4/raw --companies KR0004
# fill the ladder (UPSERT, idempotent — re-runs are no-ops). --all-periods walks every md_inbox/FY*_Q?
PY scripts/fill_period_to_disclosure.py --period FY2025_Q4 [--dry-run]
PY scripts/fill_subitems_to_disclosure.py --period FY2025_Q4 [--dry-run]
PY scripts/fill_market_subitems_to_disclosure.py --period FY2025_Q4 [--dry-run]
PY scripts/fill_market_irr_from_pdf.py [--dry-run]
# GATE — RED must be 0 (or documented); writes report_latest.json
PY scripts/validate_kics_disclosure.py
# after any master JSON change
PY scripts/build_master_xlsx.py
PY -m pytest tests/unit/
```
**Surgical single-company backfill** (avoids `fill_period`'s STALE_DELETES + cross-company item4-reconcile):
clone the inner extract loop for one code into a `scripts/_probes/*.py` and UPSERT only that company's rows.
**docling memory:** life-insurer 4Q filings (한화생명 ~740p, 동양 ~642p) can `bad_alloc` / hang minutes; keyword-
localization + per-PDF timeout + page-cap 30 mitigate. PDFs >~5MB are the danger zone.
