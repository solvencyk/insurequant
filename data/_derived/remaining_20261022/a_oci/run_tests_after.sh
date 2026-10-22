#!/bin/bash
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
cd C:/Users/sangwook.cho/Desktop/insurequant
O=data/_derived/remaining_20261022/a_oci
"$PY" -m pytest tests/test_gold_overlay_survives_rebuild.py -q > $O/pytest_gold_overlay_after.txt 2>&1
"$PY" -m pytest tests/test_master_tables_golden.py -q > $O/pytest_master_tables_golden_after.txt 2>&1
"$PY" -m pytest tests/test_rule_coverage_manifest.py -q > $O/pytest_rule_coverage_after.txt 2>&1
RUN_PL_GOLDEN=1 "$PY" -m pytest tests/test_pl_breakdown_golden.py -q > $O/pytest_pl_golden_after.txt 2>&1
echo ALLDONE > $O/run_tests_after.done
