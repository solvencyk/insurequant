# Mini resync runlog (2026-10-11)

Ticket: `inbox/publishing/20261011T2100Z__orchestrator__MULTI_2023.1Q-2026.2Q__mini_resync_after_lina_csm_pl_item4_amort_fix.md` (not edited; the orchestrator closes it).
Branch `fix/csm-product-segmented-columns`. No push, no deploy, no subagents, no docling, no golden --update, no exception registration. Copy of this log: `data/_derived/mini_resync_20261011/` holds the scripts and outputs (this file is under gitignored data/disclosure).

## Interim result (top)

- ALL STEPS DONE. Commits: `5d320c9` (xlsx 4 sheets + NB master + combo/compare panels + evidence), `812b007` (public_exports + manifest build_id 5d320c9), docs commit separate.
- Gates: validate_data_contract SUMMARY RED=0 (YELLOW 147); `MASTER_XLSX_*` 0 (census 17/17, rows 118,099, drift 0); check_master_xlsx_drift RED=0; validate_live_artifacts RED=8 = only INSPL_CENSUS_MISSING 8 (known), NB_CENSUS_MISSING 0.
- Tests: test_deploy_assets + test_push_gate_wiring + test_prepush_scope + test_rule_coverage_manifest: 241 passed, 1 skipped. Golden: test_viz_csm_waterfall_golden pass; test_viz_ifrs17_panels_golden FAIL only on csm_amort_schedule.json sha (expected: cf66dce moved 18 companies' 2025.4Q; golden --update is validation's job). The other 3 panels' hashes match.

## 1. Preflight
- No master JSON modified (git status: only data/_derived/qoq_warn.json, not a master, and a designer HTML file that was committed meanwhile). Latest data commit 396faff.
- Drift before: sheets 17/17, rows 118,090, drift cells 189, RED 6: CSM워터폴 ROW_MISSING 54 + DRIFT 15; CSM상각 ROW_MISSING 50 + DRIFT 172; 손익분해PL ROW_MISSING 33 + DRIFT 2.
- Backup `insurequant_master_tables.xlsx.bak_20261011_mini_pre` (gitignored `*.bak_*`).

## 2. xlsx sheet sync (sync_master_xlsx_sheet.py, per sheet, dry-run first; script's own verify OK every time)
| sheet | rows before -> after | added rows | changed cells | removed |
|---|---|---|---|---|
| 손익분해PL | 13,458 -> 13,491 | 33 (reinsurers 24 = item 16 x7 + item 4 x17; Lina KR0074 item 4 x9) | 2 (blank -> value: KR1101 / KR1103 2024.2Q item 16 값_당분기) | 0 |
| CSM워터폴 | 2,286 -> 2,340 | 54 (Lina, 9 quarters x 6 items) | 15 (Lina 2023.4Q/2024.4Q/2025.4Q 값_당분기 items 1-5, blank -> value) | 0 |
| CSM상각 | 570 -> 620 | 50 (Lina 2025.1Q-2026.2Q) | 172 (18 companies 2025.4Q; 170 value -> value, 2 blank -> value) | 0 |
| 신계약CSM배수 | 381 -> 390 | 9 (Lina) | 6 (Lina 2023.4Q/2024.4Q/2025.4Q 당분기 CSM and 배수, blank -> value) | 0 |
- Matches the master diffs exactly (the PL +33 row expectation holds). Invariance proof (`xlsx_invariance.py`, data_only before/after snapshot): old rows all kept (removed 0), 13 other data sheets row count + SHA identical, 요약 sheet only row-count cells corrected. Nothing outside the expected company codes changed.

## 3. NB multiple master rebuild (`build_nb_csm_multiple.py`, read first: it rebuilds the whole file from CSM_waterfall item 2 + KIDI premium_summary)
- 381 -> 390 rows. Diff (`nb_diff.txt`): added 9 = Lina only; changed existing 3 = Lina only (None -> value in 신계약CSM_당분기, 배수_당분기); every other company row unchanged (0 diffs); removed 0. Reinsurer 18 rows still null multiple (7 reinsurers have no 월납월초 source).
- Lina KR0074 now has real multiples (연누계 / 당분기): 2023.3Q 14.28 / -, 2023.4Q 14.56 / 15.24, 2024.1Q 12.59 / 12.59, 2Q 13.83 / 15.15, 3Q 12.27 / 9.87, 4Q 11.87 / 10.88, 2025.1Q 9.44 / 9.44, 2Q 9.88 / 10.26, 3Q 11.22 / 13.43, 4Q 11.54 / 12.56, 2026.1Q 9.02 / 9.02, 2Q 10.33 / 11.66. 2023.3Q 당분기 stays blank (2023.2Q CSM not loaded, held by owner decision).
- Flags printed by the builder (existing, not new): BNP Cardif 2023.4Q/2024.4Q/2025.4Q and Kakaopay 2024.4Q multiple < 1.0.
- `validate_live_artifacts` NB_CENSUS_MISSING 0.

## 4. Panel rebuild (backups in scratchpad `mini/panels_before`; the evidence is `panel_diff.txt`)
- `viz_build_ifrs17_panels.py`: csm_amort_schedule / insurance_pl_breakdown / bs_snapshot / sensitivity_heatmap all BYTE-IDENTICAL to before (ok counts 41/46, 32/32, 23/23, 38/39). Reason for csm_amort_schedule: Lina has a DART FY2025 row (rcept 20260406004539, y1 2,140.9) which the builder reads from data/dart/extracted; the master-only branch is for reinsurers (KR1101-1108) only, whose rows were already added last round. So Lina's amortization master rows (2025.1Q-2026.2Q) do not reach the viz panel. Not a bug in the data, a builder-scope observation for owner/parser: if the screen should show Lina's 2026.2Q schedule, the builder needs a rule. Builder not touched.
- `viz_build_csm_waterfall.py`: byte-identical (it reads data/dart/extracted only, not the root master).
- `viz_build_csm_combo_panel.py` (+ `--check` OK): changed 12 nodes = Lina KR0074 column 8 (nb_csm) null -> value for 11 quarters 2023.4Q-2026.2Q (e.g. 2023.4Q 1771.8, 2026.2Q 1227.9) + meta.csm_recon text (대조 273 -> 281건, 불일치 6 unchanged).
- `viz_build_compare_panel.py` (+ `--check` OK): changed 53 leaves. CSM 기말 (metric 2) Lina 9 quarters null -> value; NB multiple (metric 3) Lina 9 quarters + 생보 median 8 quarters moved by 0.1-0.9x (Lina added to the pool); 신계약 CSM (metric 15) Lina 9 quarters + reinsurers KR1101-1107 18 cells (the panel was built before NB rows for reinsurers landed in 1412aaf; the values come from that NB master, not from this round's data).

## 5. public_exports (`export_public_sheets.py` after commit 5d320c9)
- Changed files: 손익분해PL / CSM워터폴 / CSM상각 / 신계약CSM배수 + manifest.json only (11 other public sheets byte-identical). manifest build_id 1412aaf -> 5d320c9, generated_at_utc 2026-10-11T11:13:14Z. Rows: 손익분해PL 13,491 / CSM워터폴 2,340 / CSM상각 620 / 신계약CSM배수 390. Public gate (validate_live_artifacts public_exports section) 0 findings. Commit `812b007`.

## 6. Gates and tests
See the interim block at the top. Full hook `prepush_check.py` not run (as ticket says).

## Reporting notes
- Lina CSM_amortization rows exist only in master/xlsx/public_exports; no viz panel reads them (see 4).
- Own mistakes: none that touched data. First dry-run command ran each sheet twice (wasted time only).
