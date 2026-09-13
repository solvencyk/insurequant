# IFRS17 lane — quirks & traps

The failure modes that have actually cost time. Crystallized from memory + session experience
(2026-05 → 2026-06). Cross-check these before trusting an extracted value.

## Table of contents
- [Destructive rebuild on this branch](#destructive-rebuild-on-this-branch)
- [Unit normalization](#unit-normalization)
- [Sign conventions](#sign-conventions)
- [Per-company layout quirks](#per-company-layout-quirks)
- [Sensitivity is annual-only across the WHOLE universe](#sensitivity-is-annual-only-across-the-whole-universe-2026-09-01)
- [Reconciliation cross-checks](#reconciliation-cross-checks)
- [Company mapping](#company-mapping)
- [Windows / encoding](#windows--encoding)

## Destructive rebuild on this branch
`fix/csm-product-segmented-columns` had `data/dart/**/raw/` git-purged (399MB→29MB). `build_csm_waterfall_master.py`
and `build_pl_breakdown.py` rediscover companies from `data/dart/FY*/raw/` — so re-running either **collapses**
the committed masters (e.g. `csm_waterfall_master_diag.json` 1926 rows → ~12). The CSM gold gate
(`_verify_csm_golds.py`) globs repo-root `CSM waterfall_*.xlsx` and reports 0/0 here.
- **What survives:** AIA (KR0080) FY2024 raw + **all FY2025_Q4 raw** (re-downloaded) + every committed
  `data/dart/extracted/*.json` and master/viz JSON.
- **So on this branch:** fix CSM/PL cells by **disposition + `_GOLD_CELL_OVERRIDE` / surgical JSON patch**,
  never a full rebuild. FY2025 work is unblocked (raw on disk); FY2024-quarter re-parses are raw-blocked.
- **Verifiable here:** `pytest tests/unit/` + `viz_build_ifrs17_panels.py` (reads committed extracted JSON).
- See memory [[project-git-purge]]. `git checkout -- <master>` restores if a build was run by mistake.

## Unit normalization
- Sensitivity panels: **억원** (1억 = 100백만 = 1e8원). PL master: **백만원**.
- `sensitivity_extractor` / panel builder normalize via: explicit **unit cue** (억원/백만원/천원/만원/원) →
  else **cross-check** the table's base CSM against `CSM_waterfall.json` 기말 CSM (in 억원) and power-of-10 snap.
  `_finalize_sensitivity` raises a **suspect** flag if `max|ΔCSM| > 3 × total CSM`.
- DART raw income statements are in **원** — divide by 1e6 to compare with the 백만원 PL master.
- Owner unit *notes* can be wrong; when a note conflicts with the data cross-check, **data wins** (owner
  ruling 2026-06: "단위 억원으로 통일 & 데이터 판정").

## Sign conventions
- **`보험금융손익` (insurance finance income/expense) is hugely negative** for life insurers (discount unwind on
  large reserves). So `투자손익 = 투자이익 + 보험금융손익` can be a **large negative net** and still be **real** —
  do not "fix" it as a sign/column error. (푸본현대 FY2025: 투자이익 +1,452억, 보험금융손익 −2,941억,
  net 투자손익 −1,488억, full-year net loss −1,187억 — all confirmed against source.)
- Sensitivity `csm_delta` / `pl_impact`: usually **same direction** for a given risk shock, but 해지율 can flip
  vs other risks depending on the book. A site value with *opposite* csm/pl signs is often **stale data**, not a
  sign bug — re-extract the current filing and compare before concluding bug. (흥국 해지율: FY2024 csm−/pl+
  was that year's real shape; FY2025 csm−/pl− same-direction.)
- Korean accounting display: negatives shown as **△ (세모)**, not a minus sign, in any chart/table you add
  ([[feedback-samo-negative]]).

## Per-company layout quirks
| company | quirk | handling |
|---|---|---|
| 동양생명 | sensitivity table has **no CSM column** (당기손익/자본 only) | `csm_delta = null` (미공시) — NOT 0; designer renders '—' |
| NH농협 (sensitivity) | PL-only layout like 동양 | `_extract_pl_only` path |
| 흥국생명 | sensitivity = **product-row × period-band** (유배당/무배당/변액 × 위험 × shock); FY2025 added 이행현금흐름 col (6→8 value cols) | `_extract_heungkuk_product_rows` — header-derived CSM/손익 indices, reads **합계 row only** |
| 푸본현대 | FY2025 = **real full-year net loss** (not a parse error) | verify, no-op |
| 하나생명 | **audit-only**; investment shown as two numbered lines **II.투자수익 / III.투자비용** (no single 투자손익 row) → PL item17/18 fall to None | `_GOLD_CELL_OVERRIDE[(KR0097,2025.4Q)]`: item18 = II−III, item17 = 18+19 |
| 메트라이프 (KR0095) | audit-only, all PL cells null | full `_GOLD_CELL_OVERRIDE` row |
| 농협생명, 케이디비 | FY2025 sensitivity = product / 원수·출재·순액 **sub-row** layout; band/generic path mis-emits sub-rows as risks (garbage like "무배당보험 shock=22,644,512") | **phase-2**: emit 합계/순액 only, skip 무배당/유배당/변액/원수/출재; keep on FY2024 until fixed |
| 동양/메트라이프/에이비엘/처브 | FY2025 sensitivity SA=0 (no table classified) | open: `sensitivity_extractor` classification — keep FY2024 |
| 삼성화재, 흥국화재 | measurement rollforward rows ("증가분(감소분)") were mis-selected as sensitivity | `_has_shock_rows` requires a literal `%` in the shock label |
| 푸본현대/KB (validation 1135Z) | under-scale was **rollforward mis-tag**, not unit | `_has_shock_rows` guard rejects no-shock-row blocks → partial |

## Sensitivity is annual-only across the WHOLE universe (2026-09-01)

가정민감도(assumption-shock ΔCSM/손익 — 사망률·장해질병·해지율·사업비 shock) is disclosed **only
in the annual 사업보고서**, industry-wide — not a per-company gap. Verified by running
`extract_sensitivity_tables` against every one of the 24 companies that filed a FY2026_Q2
반기보고서 (`scripts/_probes/probe_20260901_sensitivity_fy2026q2_census.py`): zero contain a
real shock table. Half-year risk notes carry only IFRS9 fair-value Level-3 sensitivity (a
different topic — 관측불가 투입변수, not insurance assumptions) and/or §14(2) point-in-time
"현행 추정 가정" *values* (해약률/위험률 ranges, no shock delta). The other 14 of the 38 raw-checked
companies never file a periodic (사업/반기/분기) disclosure at all — confirmed against the live
DART API, not just the downloader's cache (`probe_20260901_sensitivity_nofiling_dart_verify.py`);
**에이아이에이생명보험(AIA)·에이아이지손해보험(AIG)** belong in this bucket too even though they
have an "ok" FY2025 panel entry — their rcept is a **연결감사보고서**(consolidated audit report),
not a periodic filing, so they'll never have an interim update either. Don't re-investigate this
per-quarter; the gate now grants sensitivity_heatmap a 3-quarter forward-hold
(`validate_data_contract.verify_provenance_sidecar(..., max_lag_quarters=3)`), so it only goes
stale again once a full year has passed with no fresh annual filing.

**Latent picker-fallback risk if the batch is ever run for a non-annual quarter without
checking first**: `_pick_sensitivity_block()`'s `pool = eligible or sens_blocks` line falls back
to the UNFILTERED candidate list when `_is_rollforward_sensitivity_caption` rejects every
candidate. 푸본현대's FY2026_Q2 raw has **12** sensitivity_analysis-tagged candidates and every
one is the CSM rollforward's "해지율/위험률/사업비율 가정 변경" sub-rows (this period's *realized*
assumption change inside the measurement rollforward — not a hypothetical shock scenario). None
carries a `%` in its shock label, so `_has_shock_rows` is False for the whole pool and the
top-priority picker signal can't discriminate — `max()` still returns *something* from that
all-garbage fallback pool. (This is presumably why 푸본현대's current FY2025 panel entry is a
hand-verified override — caption `"FY2025 보험위험 민감도 (verified override — owner 1242Z)"` —
rather than an auto-pick.) If a future quarter's batch is run unattended, verify 푸본현대's picked
block actually has a `%` shock label before trusting it.

## Reconciliation cross-checks
- `csm_amort_pl` (§2 measurement) ≈ §(5) `당기손익으로 인식한 보험계약마진`.
- 기말 total CSM (§2) ≈ §(7) amort schedule `합계`.
- PL identities (see pipeline-map.md): `item1 = item2 − item16`, `item17 = item18 + item19`,
  `영업이익(20) = item1 + item17`. A None item that breaks one of these is a **parse miss**, not a real 0 —
  derive the correct value from the closure + source, don't publish a wrong closure (the +기타사업비용 double-count
  trap: 영업이익 already nets item16 inside item1).
- Sensitivity: csm/pl sign consistency per the section above; unit suspect guard.
- Validation blind spots to actively probe ([[feedback-validation-blind-spots]], [[feedback-coverage-census-mandatory]]):
  intra-FY 기초 consistency, 0-value blindness, lower-bound plausibility, source trust, **cell-level census**
  (a missing cell is never acceptable; SKIP-on-missing defeats validation).

## Company mapping
Search DART by company name (`"메리츠화재"` is enough). Absorb 표기 차이 (`삼성생명보험`↔`삼성생명`) case-by-case.
**Never** build a permanent KR-code ↔ corp_code mapping file (owner directive,
[[feedback-ifrs17-company-mapping]], [[feedback-dont-overengineer-casual-hints]]).

## Windows / encoding
- python full path: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` (not on PATH).
- **Never inline multi-line `python -c`** — hangs the shell and wedges Workflow subagents permanently
  ([[feedback-workflow-multiline-python-hang]]). Write a `.py` file, or use Read/Grep tools.
- `sys.stdout.reconfigure(encoding="utf-8")` at the top of any script that prints Korean (console is cp949).
- All docs/inbox markdown: **UTF-8 no BOM**. If Korean would garble in your write path, write English
  ([[feedback-no-garbled-korean]]). Read back the first line after writing.
