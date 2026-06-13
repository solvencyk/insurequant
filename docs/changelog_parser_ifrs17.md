# Parser Changelog — IFRS17 lane (Stage 2)

> Last updated: 2026-06-13 · Stage 2/5 — parser (ifrs17 lane)
> Prompt: docs/agents/claude-agent-parser.md (shared) + docs/domains/claude-agent-ifrs17.md · TODO: TODO_parser_ifrs17.md

IFRS17 extraction history: DART body XML → CSM_waterfall / PL_breakdown / NB-CSM-multiple masters.
Code: `src/ifrs17/` (csm / measurement / insurance_pl / reinsurance / bs_snapshot / sensitivity extractors +
`scoring.py` config layer). Validators: CSM golds, PL golds, csm_waterfall / pl_bridge crosscheck.

**Pre-split combined history (before 2026-06-13): [`changelog_parser.md`](changelog_parser.md)** (frozen).
Convention: see [`docs/agents/doc-style.md`](agents/doc-style.md).

---

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
