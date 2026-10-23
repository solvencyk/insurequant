#!/bin/bash
# usage: run_tests.sh <tag> [pl_golden]   (final run: everything except the PL golden, which already passed on the loaded state: pytest_pl_golden_after1.txt)
# NOTE: the "rc=" shown here is the exit code of the pytest line captured in $?; the verdict is the last line of each pytest_<test>_<tag>.txt
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
cd C:/Users/sangwook.cho/Desktop/insurequant
O=data/_derived/remaining_20261022/e23_d1_d3/kr0009_hyundai
T=$1
for t in test_gold_overlay_survives_rebuild test_identity_registry test_identity_tautology test_master_tables_golden test_viz_ifrs17_panels_golden test_viz_csm_waterfall_golden test_dividend_golden test_deploy_assets test_rule_coverage_manifest; do
  S=$(date +%H:%M:%S)
  "$PY" -m pytest tests/$t.py -q --no-header -p no:cacheprovider < /dev/null > $O/pytest_${t}_$T.txt 2>&1
  RC=$?
  echo "[$S -> $(date +%H:%M:%S)] $t rc=$RC : $(tail -1 $O/pytest_${t}_$T.txt)"
done
if [ "$2" = "pl_golden" ]; then
  S=$(date +%H:%M:%S)
  RUN_PL_GOLDEN=1 "$PY" -m pytest tests/test_pl_breakdown_golden.py -q --no-header -p no:cacheprovider < /dev/null > $O/pytest_pl_golden_$T.txt 2>&1
  RC=$?
  echo "[$S -> $(date +%H:%M:%S)] pl_golden rc=$RC : $(tail -1 $O/pytest_pl_golden_$T.txt)"
fi
echo ALLDONE
