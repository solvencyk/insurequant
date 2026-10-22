#!/bin/bash
# usage: run_tests.sh <before|after>  (one at a time, strictly sequential)
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
cd C:/Users/sangwook.cho/Desktop/insurequant
O=data/_derived/remaining_20261022/e19_latest_comparative/apply
T=$1
for t in test_gold_overlay_survives_rebuild test_master_tables_golden test_identity_registry test_rule_coverage_manifest; do
  echo "[$(date +%H:%M:%S)] start $t"
  "$PY" -m pytest tests/$t.py -q --no-header -p no:cacheprovider < /dev/null > $O/pytest_${t}_$T.txt 2>&1
  echo "[$(date +%H:%M:%S)] done $t rc=$?"
done
echo "[$(date +%H:%M:%S)] start pl_golden"
RUN_PL_GOLDEN=1 "$PY" -m pytest tests/test_pl_breakdown_golden.py -q --no-header -p no:cacheprovider < /dev/null > $O/pytest_pl_golden_$T.txt 2>&1
echo "[$(date +%H:%M:%S)] done pl_golden rc=$?"
echo ALLDONE
