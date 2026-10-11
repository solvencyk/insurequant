# Mini resync 2 runlog (2026-10-12)

Ticket: `inbox/publishing/20261012T0500Z__orchestrator__MULTI_2023.1Q-2026.2Q__mini_resync_2_reinsurer_resweep.md` (not edited). Branch fix/csm-product-segmented-columns. No push/deploy/subagents/docling/golden --update/exception registration.

## Interim result (top)
- ALL STEPS DONE. Commits: `b4b6a71` (xlsx 7 sheets + NB master + combo/compare panels + evidence), `5079688` (public_exports, manifest build_id b4b6a71), docs commit separate.
- Gates: validate_data_contract SUMMARY RED=102 (all CONCEPT_MIXED_DISCLOSURE_INTO_DART; before the round 109 = 102 + MASTER_XLSX 7), YELLOW 147; MASTER_XLSX_* 0 (drift 0 cells, 120,507 rows); validate_live_artifacts RED=0, YELLOW 25 baselined (INSPL_CENSUS_MISSING 15 etc.), NB_CENSUS_MISSING 0, public_exports section 0 findings.
- Tests: test_deploy_assets + test_push_gate_wiring + test_prepush_scope 142 passed, 1 skipped. Golden viz (ifrs17 panels + csm_waterfall) 2 passed (the earlier csm_amort_schedule sha failure was already resolved by validation).

## 1. Preflight
- Masters == HEAD (git status: only data/_derived/qoq_warn.json modified, not a master). Latest data commit 3727438 (+ 57b7d78 CSM family).
- Drift before (check_master_xlsx_drift): RED 7: 17BS ROW_MISSING 49, 가정민감도 6, CSM워터폴 18, CSM상각 15, 손익분해PL 303 + DRIFT 25 cells (15 rows), 보험계약부채 110. validate_data_contract before: RED=109 = CONCEPT_MIXED_DISCLOSURE_INTO_DART 102 + MASTER_XLSX_ROW_MISSING 6 + MASTER_XLSX_DRIFT 1 (YELLOW 147).
- Master diff vs 812b007 (`master_diff.txt`) equals the drift counts exactly. NOTE for ticket: PL corrected cells are 25 (값 11 cells in 11 rows + 값_당분기 14 cells in 14 rows; 15 distinct rows: KR1102 / KR1103 / KR1105), not 11+4.
- Backups: insurequant_master_tables.xlsx.bak_20261012_mini2_pre, .bak_20261012_mini2_nb (gitignored *.bak_*).

## 2. xlsx sheet sync (sync_master_xlsx_sheet.py per sheet; script verify OK each time)
| sheet | rows before -> after | added | changed cells | removed |
|---|---|---|---|---|
| 손익분해PL | 13,491 -> 13,794 | 303 (KR1101 41, KR1102 42, KR1103 41, KR1104 40, KR1105 41, KR1106 42, KR1107 41, KR1108 15) | 25 (all value->value; KR1102 10, KR1103 7, KR1105 8) | 0 |
| 17BS | 10,967 -> 11,016 | 49 (KR1101 11, KR1103 24, KR1104 6, KR1107 8) | 0 | 0 |
| CSM워터폴 | 2,340 -> 2,358 | 18 (KR1104 6, KR1105 6, KR1107 6) | 0 | 0 |
| CSM상각 | 620 -> 635 | 15 (KR1101/1102/1106 x5) | 0 | 0 |
| 가정민감도 | 311 -> 317 | 6 (KR1104 2023.4Q) | 0 | 0 |
| 보험계약부채 | 6,225 -> 6,335 | 110 (KR1101 50, KR1104 36, KR1103 8, KR1105 8, KR1107 8) | 0 | 0 |
| 신계약CSM배수 | 390 -> 393 | 3 | 0 | 0 |
- Invariance (`xlsx_invariance.txt`): removed 0 everywhere, all other 10 data sheets byte/sha IDENTICAL, 요약 differs only in row-count cells (`summary_diff.txt`). Drift after: RED 0, 120,507 rows, 0 cells.

## 3. NB multiple master (`build_nb_csm_multiple.py`)
- 390 -> 393 rows: added KR1104 2025.4Q (신계약CSM 4.32), KR1105 2025.4Q (1,077.92), KR1107 2023.4Q (128.63); all reinsurers have null 월납월초 and null multiple. Existing 390 rows: 0 changed, 0 removed (`nb_diff.txt`); Lina unchanged. Builder flags are the same 4 existing (BNP Cardif x3, Kakaopay 2024.4Q <1.0).

## 4. Panels (backups in scratchpad panels_before and $D/panels_before for combo/compare; evidence panel_diff.txt, panel_scope.txt, panel_scope_check.txt)
- `viz_build_ifrs17_panels.py`: csm_amort_schedule / insurance_pl_breakdown / bs_snapshot / sensitivity_heatmap BYTE-IDENTICAL (ok 41/46, 32/32, 23/23, 38/39). Reason (panel_scope_check.txt): the master-only branch loads only each reinsurer's latest quarter (2025.4Q) and every new amort/sensitivity row is 2023.4Q (KR1101/1102/1106 amort, KR1104 sensitivity), so nothing reaches the panel. Builder not touched.
- `viz_build_csm_waterfall.py`: byte-identical (reads data/dart/extracted only; reinsurers not in this panel by design).
- `viz_build_csm_combo_panel.py` (+ --check OK): 52 nodes changed, reinsurers only (KR1101, KR1103, KR1104, KR1105, KR1107): older-quarter columns filled from the new ILP rows (portfolio liability columns and the 2023.4Q column). meta csm_recon 281 -> 287 matched, mismatches 6 unchanged; lic_recon real 388 -> 401, estimated 78 -> 83, none 59 -> 52. Lina and all 42 other companies unchanged.
- `viz_build_compare_panel.py` (+ --check OK): 137 leaves changed, reinsurers only, no other company. By metric: 기말 CSM (2) 3, 보험손익 (4) 1, 당기순이익 (5) 4 (PL corrections), 신계약 CSM (15) 3, 투자손익 (16) 101 (new PL item 17 rows), 손해율 PV (12) 18 + loss_curve 7 reinsurers. Metric 12 and loss_curve come from the previous round's panel_loss_ratio reinsurer rows (66e6156), which the compare panel had not picked up yet; not this round's data.

## 5. public_exports (`export_public_sheets.py` after commit b4b6a71)
- Changed: 17BS 11,016 / CSM워터폴 2,358 / CSM상각 635 / 가정민감도 317 / 신계약CSM배수 393 / 손익분해PL 13,794 / 보험계약부채 6,335 + manifest.json (build_id 5d320c9 -> b4b6a71, generated_at_utc 2026-10-11T19:21:54Z). Other sheets byte-identical. Commit `5079688`.

## 6. Gates and tests
See the interim block at the top. Full hook prepush_check.py and full pytest not run (as ticket says). Outputs: gate_data_contract_before.txt / gate_data_contract.txt / gate_live_artifacts.txt / gate_tests.txt / gate_golden_viz.txt.

## Reporting notes
- Ticket said PL corrections = 정정 11 + 파생 4; actual = 25 cells (값 11 + 값_당분기 14) in 15 rows (KR1102 10, KR1103 7, KR1105 8 cells).
- ifrs17 viz panels need a builder rule if the screen should show reinsurer history quarters: the master-only branch carries only the latest quarter per reinsurer. Builder not touched.
- Own mistakes: none that touched data.
