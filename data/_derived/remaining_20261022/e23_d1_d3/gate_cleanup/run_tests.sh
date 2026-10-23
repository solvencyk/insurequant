#!/bin/bash
# usage: run_tests.sh <tag>  (strictly sequential)
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
cd C:/Users/sangwook.cho/Desktop/insurequant
O=data/_derived/remaining_20261022/e23_d1_d3/gate_cleanup/tests_$1
mkdir -p $O
for t in test_master_tables_golden test_identity_tautology test_identity_registry test_deploy_assets test_push_gate_wiring test_rule_coverage_manifest; do
  echo "[$(date +%H:%M:%S)] start $t"
  "$PY" -m pytest tests/$t.py -q --no-header -p no:cacheprovider < /dev/null > $O/$t.txt 2>&1
  echo "[$(date +%H:%M:%S)] done $t rc=$?"
done
echo ALLDONE
