#!/bin/bash
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
cd C:/Users/sangwook.cho/Desktop/insurequant
O=data/_derived/remaining_20261022/e23_d1_d3/verify_final_gates/tests
mkdir -p $O
for t in test_rule_coverage_manifest test_gold_overlay_survives_rebuild test_identity_tautology test_identity_registry test_master_tables_golden test_viz_ifrs17_panels_golden test_viz_csm_waterfall_golden; do
  echo "[$(date +%H:%M:%S)] start $t"
  "$PY" -m pytest tests/$t.py -q --no-header -p no:cacheprovider < /dev/null > $O/$t.txt 2>&1
  echo "[$(date +%H:%M:%S)] done $t rc=$?"
done
echo ALLDONE
