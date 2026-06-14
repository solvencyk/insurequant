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
  whole-cohort mvp-vs-full diff CHANGED 0. Remaining (separate): 흥국생명 product-as-rows shock col (TODO F16,
  designer-linked); validation 단위/비율 게이트 rule (parser-side guard done).

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
