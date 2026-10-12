# Final resync runlog (2026-10-12)

Ticket: `inbox/publishing/20261012T1330Z__orchestrator__MULTI_2023.1Q-2026.2Q__final_resync_before_push.md` (not edited). Branch fix/csm-product-segmented-columns. No push/subagents/docling/golden --update/exception registration. Masters were read-only.

## Result
- Commits: `538cbe7` (xlsx + 3 panels + evidence), `dee37c2` (public_exports, manifest build_id 538cbe7), docs commit separate.
- Preflight: parser-kics commit `acd351a` already landed (kics_disclosure.json clean) before the K-ICS sheet sync, which was done last.
- Drift before: RED 7 (17BS 6 cells, K-ICS ROW_MISSING 16 + DRIFT 4, CSM상각 18, PL ROW_MISSING 7 + DRIFT 1, 보험계약부채 18). After: RED 0, 120,692 rows, 0 cells.
- Gates: validate_data_contract RED=0 YELLOW=152; validate_live_artifacts RED=0, YELLOW baselined 25 (INSPL_CENSUS_MISSING 15), STALE_BASELINE 0; validate_master_tables --no-build exit 2 (pinned by test_master_tables_golden, which passes); golden master_tables + ifrs17 panels + csm_waterfall 3 passed; test_deploy_assets + test_push_gate_wiring + test_prepush_scope 142 passed, 1 skipped. Golden mismatches: none.

## Panels (before = git HEAD / saved copy; diffs in panel_*_diff.txt)
- `viz_build_persistency_lossratio_panels.py`: --check failed before (disk 206,065 vs rebuild 206,474 bytes); rebuilt, --check OK. 41 nodes, all companies KR1101-KR1107 (reinsurers): segment keys now life / long-term non-life, old `손해보험` and blank-segment nodes deleted, plus meta.source_sha12. panel_persistency unchanged.
- `viz_build_ifrs17_panels.py` (4 panels) and `viz_build_csm_waterfall.py`: byte-identical to HEAD.
- `viz_build_csm_combo_panel.py` (+--check OK): 21 nodes, Chubb KR0100 only (portfolio liability columns, 2023.1Q-2025.3Q); meta lic_recon: real 401 and sidecar 30 unchanged, estimated 83->85, none 52->50, est_unreliable updated; csm_recon unchanged.
- `viz_build_compare_panel.py` (+--check OK): 2 leaves: KR0049 K-ICS ratio 2024.3Q 286.4->286.5; KR1101 investment profit null->0 (restored printed-zero PL cell).
- `viz_build_ifrs17_kpis.py`: rebuilt 213 nodes across ~40 companies from the older amortization-schedule correction (cf66dce), not from this round; no HTML reads downstream_kpis.json. Reverted with git checkout; rebuilt copy kept as `downstream_kpis.rebuilt_NOT_COMMITTED.json`. Owner/designer may decide whether the file should be refreshed.
- `viz_build_nb_csm_ratio.py`: skipped. It reads IR text artifacts and also writes templates/ and embed.js; none of the masters changed today feed it.

## xlsx (backup insurequant_master_tables.xlsx.bak_20261012_final_pre, gitignored)
| sheet | rows | added | changed cells | removed |
|---|---|---|---|---|
| 17BS | 11,016 | 0 | 6 (KR0100 item 20, value->value) | 0 |
| CSM상각 | 635 | 0 | 18 (blank->value 8, value->value 10) | 0 |
| 손익분해PL | 13,794 -> 13,801 | 7 (KR1101 1, KR1103 2, KR1105 2, KR1107 2) | 1 (KR1105 2023.3Q item 21 값_당분기) | 0 |
| 보험계약부채 | 6,335 | 0 | 18 (KR0100 value->value) | 0 |
| K-ICS공시 | 29,992 -> 30,008 | 16 (KR1107 2025.3Q + 2026.2Q items 47-54) | 4 (KR0049 2024.3Q items 3, 4, 27) | 0 |
- Other 12 data sheets byte/sha identical; 요약 differs only in row-count cells (K-ICS공시, 손익분해PL, 합계). Note: the invariance script treats 보험계약부채 as removed 18/added 18 only because its key list spans the 값 column; the sync log shows 18 in-place cell edits and row count unchanged.

## public_exports
Changed: 17BS, CSM상각, K-ICS공시, 보험계약부채, 손익분해PL + manifest (build_id c3ebcc3 -> 538cbe7, K-ICS공시 rows 30008, 손익분해PL rows 13801). The 3 sheets taken off the download list were not touched.
