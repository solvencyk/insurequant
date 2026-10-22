#!/bin/bash
cd /c/Users/sangwook.cho/Desktop/insurequant
V=data/_derived/remaining_20261022/e20_held_and_remaining/verify
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
for t in test_master_tables_golden test_gold_overlay_survives_rebuild test_identity_registry test_identity_tautology test_rule_coverage_manifest; do
  "$PY" -m pytest tests/$t.py -q -p no:cacheprovider -rf < /dev/null > $V/pytest_$t.txt 2>&1
  echo "rc=$?" >> $V/pytest_$t.txt
  echo "$t: $(tail -3 $V/pytest_$t.txt | tr '\n' ' ')"
done
