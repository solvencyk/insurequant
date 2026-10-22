#!/bin/bash
cd /c/Users/sangwook.cho/Desktop/insurequant
V=data/_derived/remaining_20261022/e21_ready25/verify
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
RUN_PL_GOLDEN=1 "$PY" -m pytest tests/test_pl_breakdown_golden.py -x -q -p no:cacheprovider < /dev/null > $V/pytest_pl_golden.txt 2>&1
echo "rc=$?" >> $V/pytest_pl_golden.txt
for t in test_master_tables_golden test_gold_overlay_survives_rebuild test_identity_registry test_identity_tautology test_rule_coverage_manifest test_viz_ifrs17_panels_golden test_viz_csm_waterfall_golden; do
  "$PY" -m pytest tests/$t.py -q -p no:cacheprovider -rf < /dev/null > $V/pytest_$t.txt 2>&1
  echo "rc=$?" >> $V/pytest_$t.txt
done
echo ALLDONE > $V/pytest_done.txt
