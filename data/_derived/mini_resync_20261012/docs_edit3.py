# -*- coding: utf-8 -*-
from pathlib import Path
D = Path(__file__).resolve().parent
p = D / "runlog.md"
t = p.read_text(encoding="utf-8")
t = t.replace("- Steps 1-3 DONE (preflight, xlsx 7 sheets, NB). Steps 4-6 pending.",
"- ALL STEPS DONE. Commits: `b4b6a71` (xlsx 7 sheets + NB master + combo/compare panels + evidence), `5079688` (public_exports, manifest build_id b4b6a71), docs commit separate.\n"
"- Gates: validate_data_contract SUMMARY RED=102 (all CONCEPT_MIXED_DISCLOSURE_INTO_DART; before the round 109 = 102 + MASTER_XLSX 7), YELLOW 147; MASTER_XLSX_* 0 (drift 0 cells, 120,507 rows); validate_live_artifacts RED=0, YELLOW 25 baselined (INSPL_CENSUS_MISSING 15 etc.), NB_CENSUS_MISSING 0, public_exports section 0 findings.\n"
"- Tests: test_deploy_assets + test_push_gate_wiring + test_prepush_scope 142 passed, 1 skipped. Golden viz (ifrs17 panels + csm_waterfall) 2 passed (the earlier csm_amort_schedule sha failure was already resolved by validation).")
t += """
## 5. public_exports (`export_public_sheets.py` after commit b4b6a71)
- Changed: 17BS 11,016 / CSM워터폴 2,358 / CSM상각 635 / 가정민감도 317 / 신계약CSM배수 393 / 손익분해PL 13,794 / 보험계약부채 6,335 + manifest.json (build_id 5d320c9 -> b4b6a71, generated_at_utc 2026-10-11T19:21:54Z). Other sheets byte-identical. Commit `5079688`.

## 6. Gates and tests
See the interim block at the top. Full hook prepush_check.py and full pytest not run (as ticket says). Outputs: gate_data_contract_before.txt / gate_data_contract.txt / gate_live_artifacts.txt / gate_tests.txt / gate_golden_viz.txt.

## Reporting notes
- Ticket said PL corrections = 정정 11 + 파생 4; actual = 25 cells (값 11 + 값_당분기 14) in 15 rows (KR1102 10, KR1103 7, KR1105 8 cells).
- ifrs17 viz panels need a builder rule if the screen should show reinsurer history quarters: the master-only branch carries only the latest quarter per reinsurer. Builder not touched.
- Own mistakes: none that touched data.
"""
p.write_text(t, encoding="utf-8")
