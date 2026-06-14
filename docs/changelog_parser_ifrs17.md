# Parser Changelog — IFRS17 lane (Stage 2)

> Last updated: 2026-06-13 · Stage 2/5 — parser (ifrs17 lane)
> Prompt: docs/agents/claude-agent-parser.md (shared) + docs/domains/claude-agent-ifrs17.md · TODO: TODO_parser_ifrs17.md

IFRS17 extraction history: DART body XML → CSM_waterfall / PL_breakdown / NB-CSM-multiple masters.
Code: `src/ifrs17/` (csm / measurement / insurance_pl / reinsurance / bs_snapshot / sensitivity extractors +
`scoring.py` config layer). Validators: CSM golds, PL golds, csm_waterfall / pl_bridge crosscheck.

**Pre-split combined history (before 2026-06-13): [`changelog_parser.md`](changelog_parser.md)** (frozen).
Convention: see [`docs/agents/doc-style.md`](agents/doc-style.md).

---

## 2026-06-14 — CSM sensitivity panel: column-map / unit / 손보-recovery (inbox 20260614T0712Z)

Owner live-site QA on the CSM sensitivity pipeline — fixed 3 glitches in
`scripts/viz_build_ifrs17_panels.py` (panel parser only; no extractor change):
- **G4b (column mapping)**: `_extract_sensitivity_band` used a fixed LEFT-anchored csm_idx, so
  rowspan-elided 2nd+ risk rows (기준금액 columns dropped) shifted → wrong ΔCSM + null PL. Now RIGHT-anchors
  (negative idx) for the standard 기타포괄손익-trailing layout; other layouts (위험경감/product-row) guarded, no regression.
- **G6 (units → 억원, data-determined)**: cue (억원/백만원/천원/만원) else cross-check table base CSM vs
  `CSM_waterfall.json` total CSM (억원) → power-of-10 snap. Owner's notes were BOTH wrong: 삼성=백만원 (not 만원),
  현대=천원 (not 원). 현대 사망률 ΔCSM −853억 ≈ 삼성 −1,334억 (640× anomaly gone). Output carries
  `unit/unit_detected/unit_source`. Sanity guard: max|ΔCSM| > 3× total CSM → `unit_source=suspect` + null + warning
  (메트라이프 default-백만원 −59조 blocked).
- **G7 (missing 손보)**: panel read only `_sensitivity_mvp.json` (is_mvp dropped valid tables) + the picker
  preferred CSM-less tables. Now reads full `_sensitivity.json` (build_panel skips non-rcept K-ICS files), picker
  prefers a 보험계약마진 column, methodology-table penalty, + a PL-only handler (NH 출재경감 당기손익). Recovered
  메리츠/DB손해/KB/NH (한화 = 별첨, legit partial) + bonus AIA/케이비라이프. **0 regressions, 25/28 ok.**
- Verify: production build touched only `sensitivity_heatmap.json` (other panels byte-identical); pytest 110;
  whole-cohort mvp-vs-full diff CHANGED 0.
- **Follow-up (same session, decision-free sweep):** F16 흥국생명 product-as-rows **DONE** — new
  `_extract_heungkuk_product_rows` + `_is_heungkuk_csm_pl_capital_layout` (4th path, 흥국-specific bare-'CSM'×2 +
  손익효과 + 자본효과 header guard) → 6 proper risk scenarios (사망률/해지율/사업비 × 상승/하락; was garbage
  risk='건강보험' shock='5,852'). status unchanged (was already ok), 0 regression, other panels byte-identical,
  pytest 110. 미래에셋생명·신한라이프 confirmed **legit-absent** (no insurance-risk CSM sensitivity table in body
  — only market-risk/pension; current unavailable/partial correct). **BLOCKED on this branch (raw DART purged):**
  closing-5 label variants / 흥국화재 NEW 2025.4Q-2026.1Q / 흥국생명 2026.1Q doubling — every target (사,분기) raw
  XML was history-purged → can't reproduce or verify; owner must restore raw (backup `insurequant_git_backup_20260614`)
  or run on a branch that still has it. NOTE: gold gate also non-runnable here (`_verify_csm_golds.py` globs repo-root
  `CSM waterfall_*.xlsx` → 0/0; `build_csm_waterfall_master.py` collapses the committed diag to 1 company).
- **Follow-up (validation reparse 20260614T1135Z):** 푸본현대 csm_delta under-scale (csm 9.86억 vs pl 1164.85억)
  root cause was NOT a unit/ratio bug — all 4 of its SA-tagged blocks are the SAME measurement rollforward
  ("기말 보험계약부채(자산)", no ± shock rows); the panel read its rollforward columns as csm/pl = garbage. Fix:
  `_has_shock_rows` (a real sensitivity table has X% 증가/감소/상승/하락 rows) → added as the top picker signal
  AND a guard in extract_sensitivity that returns `partial` when the picked block has no shock rows. Also caught
  KB손해 (5 mis-tagged '(14) 가정변경…변동 내역' rollforwards, no real shock table). 푸본현대 + KB ok→partial
  (garbage→honest); 미래에셋/신한/한화 unchanged; **0 regression on the 23 real ok companies**; pytest 110. This
  removes the peer-scale outlier so validation's SENSITIVITY_UNIT_SANITY should clear. (NB: high within-row
  |csm/pl| for 현대/삼성/한화생명 is legit — CSM absorbs the shock, not an error.)

## 2026-06-14 — REFACTOR 6/6 (bs_snapshot/sensitivity externalization) + GOLDEN-E2E expansion

Finished the owner `parser_refactor` backlog (inbox `20260613T0200Z`) for the ifrs17 lane:
- **REFACTOR-2 → 6/6**: externalized bs_snapshot + sensitivity scoring keywords (15 lists) to
  `data/ifrs17/table_scoring_keywords.yaml` via `scoring.py` `load_scoring().extra` (bespoke sets — all
  ride in `.extra`, no standard fields). Module constant names unchanged → consumers
  (`viz_build_ifrs17_panels`, batch scripts) untouched. intra-block DEDUP `&bs_slices` anchor
  (`_HEADER_BS_SLICES`==`_ROW_SLICES`). New golden tests `test_{bs_snapshot,sensitivity}_extractor.py`.
- **GOLDEN-E2E**: hermetic multi-table fixtures for measurement/insurance_pl/reinsurance (삼성화재
  20250311001055 real values, 2 decoys + 1 genuine), proving table SELECTION end-to-end. +3 tests.
- **Verification** (main session re-ran, did not trust subagent report): `pytest tests/unit/` **110 passed**;
  independent HEAD-vs-config byte-identity **15/15** (non-circular — compares git HEAD constants, not the
  golden literals); E2E asserted values 9/9 present in source JSON; 6-extractor diff is import + constant-load
  only (logic unchanged, −280/+74).
- **Remaining**: REFACTOR-3 slice2 (`src/solvency/parser/` column-picker → registry) is K-ICS/solvency lane,
  out of ifrs17 session scope → kics lane to pick up.
- **Method note**: a workflow subagent HUNG the Windows shell on a multi-line `python -c "..."` JSON dump
  (default Bash timeout never fired → runner wedged, unstoppable via TaskStop). Recovery: drove Phase 2 via a
  hardened fresh Agent (script files / Read tool, never inline multi-line `python -c`). Bake this into future
  fan-out prompts.

## 2026-06-13 — Lane split
Parser forked into two parallel lanes (kics / ifrs17). IFRS17-scoped history starts here; older IFRS17 entries
remain in the frozen combined `changelog_parser.md`. In-flight: REFACTOR-1/2 (scoring config layer, 4/6
extractors + golden tests). Open work: [`TODO_parser_ifrs17.md`](../TODO_parser_ifrs17.md).
