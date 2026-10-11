# Pre-push final round runlog (validation, 2026-10-11, ticket 20261011T2200Z)

## Verdict (top)

Pushing now at HEAD (after this round's commits) is **BLOCKED by exactly one gate item**: `validate_live_artifacts` RED=8
(`INSPL_CENSUS_MISSING` for 8 companies that are new in PL_breakdown.json: MyBrown, Munich Re, Swiss Re Asia, SCOR, RGA, General Re, Pacific Life Re, Hannover).
Every other hook item is clear. Fix = owner decision: register the 8 (proposal `data/_derived/pre_push_final_20261011/pre_push_final_proposed_baseline_inspl_20261011.json`, not applied) or narrow the census.

## Full hook dry run (`scripts/prepush_check.py`, scope FULL, 2846 changed paths, 1491 s pytest + gates, total ~28 min)

| hook item | result |
|---|---|
| 1 data-contract hard gate | RED=0 YELLOW=147 (provisional=False) |
| 1b K-ICS rule gate | exit 0, blocking RED 0 (RED 56 all documented), census MISSING_CELLS(RED)=0 |
| 1c domain gates | csm_continuity 0 · kics_rate_sensitivity 0 · nb_csm_multiple 0 · csm_waterfall 0 · **live_artifacts exit 2 (RED=8)** · disclosure_freshness 0 · stale_quarter_tables 0 |
| 1d DART raw coverage | 0 lost |
| 1e golden input fingerprint | RED=0 (after this round's `--update`; was RED=3 before) |
| 1f deployed JS runtime | clear |
| 3 inbox hygiene | 0 mechanical violations |
| 4 offline tests | 772 passed, 1 skipped (FULL_COVERAGE_SWEEP=1) |

## Goldens (before/after)

| golden | before | action | why |
|---|---|---|---|
| test_kics_rules_golden | pass | none | |
| test_post_transition_golden | pass | none | |
| test_dividend_golden | pass | none | |
| test_viz_csm_waterfall_golden | pass | none | |
| test_viz_ifrs17_panels_golden | FAIL (csm_amort_schedule only) | `--update` | sha 2c8cfdd9 -> 2ee72b7f = intended effect of cf66dce; 3 other panel hashes unchanged; committed file == fresh rebuild (sha 2ee72b7f) |
| test_master_tables_golden | FAIL (SUMMARY) | `--update` | coverage_hole 3->2PL, new `pl_src_absent:1ok/0red` (Hannover 2025.3Q), closing 381->390P (Lina CSM), csm_amort_identity 354P/5PIN/22S -> 380P/5PIN/5S, qoq_warn 252->262Y; exit code stays 2 (Seoul Guarantee PL holes) |
| builder_input_fingerprints | RED=3 (viz_ifrs17_panels) | `--update` | only the viz_ifrs17_panels entry moved |
| test_pl_breakdown_golden (RUN_PL_GOLDEN=1, 293 s) | pass | none | master f9c841fd... and coverage 9cc06bdc... byte-unchanged |
| test_ifrs17_bs_golden (~8 min) | not run | skipped | IFRS17_BS.json sha fa37d88c... == golden sha; BS input fingerprint ok; master last changed 10-11 16:57, golden refreshed 17:31 |

## Offline test failures

`tests/test_disclosure_raw_pdf_wiring.py` 2 failures (`bspl_apply_findpage.py`, `bspl_apply_render.py`): this file is **not** part of the hook bundle
(prepush_check `fast` list + `tests/unit/`), so it never blocked a push. Fixed anyway with the minimal script-side change (use `disclosure_pdfs()`; no exception registered):
now 466 passed. `test_deploy_assets` / `test_push_gate_wiring` still pass (545 passed together).

## Report-only items (no registration done)

| item | current effect | recommendation |
|---|---|---|
| live_artifacts `INSPL_CENSUS_MISSING` 8 | **the only hook blocker** | owner: register 8 lines (proposal file) or narrow census to DART-filing companies |
| Seoul Guarantee 2024.2Q/3Q PL `HOLE-PL` (통째) 2 | `validate_master_tables` section 0 only; golden pins exit 2; not a data-contract RED, not in hook | owner: add to `_PL_SOURCE_ABSENT` (NO_RAW_PDF final) or leave |
| Lina KR0074 CSM 2023.1Q/2Q hold | not a gate finding; adding a 7th quarter would make active_min=7 -> MASTER_HOLE | owner decision on extending from 2024.1Q in one go (TODO_parser_ifrs17) |
| split-table 5 companies (Lina, AIA, Chubb, MetLife, BNP Cardif) | `AMORT_TOTAL_VS_CLOSING_CSM_BAND` 4 YELLOW (baselined, STALE 0) | parser ticket: merge the second half (9 years~total) |
| Hanwha Life consolidated table chosen (panel 88,752 vs master 87,136.5 = +1.85%) | display only, no gate | parser ticket: separate-first rule |
| other YELLOW unchanged | live_artifacts YELLOW(baselined) 17 | none |

Models: Sonnet 5.5. Backups of viz JSONs and PL master in the session scratchpad (not committed); working tree restored byte-identical after every golden run.
