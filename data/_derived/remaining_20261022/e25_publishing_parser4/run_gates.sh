#!/bin/bash
# sequential gates, stdin from /dev/null
cd C:/Users/sangwook.cho/Desktop/insurequant
E=data/_derived/remaining_20261022/e25_publishing_parser4
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
export PYTHONIOENCODING=utf-8
$PY scripts/check_master_xlsx_drift.py < /dev/null > $E/drift_after.txt 2>&1
$PY scripts/validate_data_contract.py < /dev/null > $E/data_contract_after.txt 2>&1
$PY scripts/validate_master_tables.py --no-build < /dev/null > $E/master_tables_after.txt 2>&1
$PY scripts/validate_live_artifacts.py < /dev/null > $E/live_artifacts_after.txt 2>&1
$PY scripts/validate_golden_input_fingerprints.py < /dev/null > $E/gate_golden_fp.txt 2>&1
for t in test_master_tables_golden test_viz_ifrs17_panels_golden test_viz_csm_waterfall_golden test_deploy_assets test_push_gate_wiring test_loss_unit_panels_vs_master test_rule_coverage_manifest; do
  $PY -m pytest tests/$t.py -q < /dev/null > $E/pytest_$t.txt 2>&1
done
echo done > $E/gates_done.txt
