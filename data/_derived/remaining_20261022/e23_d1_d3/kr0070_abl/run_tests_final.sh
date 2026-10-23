#!/bin/bash
# usage: run_tests_final.sh <tag>  (strictly sequential; all tests except the 6-minute PL golden, which already passed on the loaded state: pytest_pl_golden_after1.txt)
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
cd C:/Users/sangwook.cho/Desktop/insurequant
O=data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl
T=$1
for t in test_gold_overlay_survives_rebuild test_identity_registry test_master_tables_golden test_viz_ifrs17_panels_golden test_viz_csm_waterfall_golden test_rule_coverage_manifest test_dividend_golden; do
  echo "[$(date +%H:%M:%S)] start $t"
  "$PY" -m pytest tests/$t.py -q --no-header -p no:cacheprovider < /dev/null > $O/pytest_${t}_$T.txt 2>&1
  echo "[$(date +%H:%M:%S)] done $t rc=$?"
done
echo ALLDONE
