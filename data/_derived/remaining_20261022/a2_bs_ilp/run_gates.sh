#!/bin/bash
# usage: run_gates.sh before|after   (sequential, one process at a time)
cd C:/Users/sangwook.cho/Desktop/insurequant
T=$1
E=data/_derived/remaining_20261022/a2_bs_ilp
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
run() { n=$1; shift; s=$(date +%s); "$@" > $E/gate_${T}_$n.txt 2>&1; echo "exit $?  secs $(( $(date +%s)-s ))" >> $E/gate_${T}_$n.txt; echo "$n done"; }
[ "$T" = after ] && run validate_master_tables $PY scripts/validate_master_tables.py --no-build
run data_contract $PY scripts/validate_data_contract.py
run csm_continuity $PY scripts/validate_csm_continuity.py
run ilp_lic $PY scripts/validate_insurance_liability_lic.py
run ilp_portfolio $PY scripts/validate_insurance_liability_portfolio.py
run fingerprints $PY scripts/validate_golden_input_fingerprints.py
run viz_panels $PY -m pytest tests/test_viz_ifrs17_panels_golden.py -q -p no:cacheprovider
run viz_waterfall $PY -m pytest tests/test_viz_csm_waterfall_golden.py -q -p no:cacheprovider
run master_tables_golden $PY -m pytest tests/test_master_tables_golden.py -q -p no:cacheprovider
run rule_coverage $PY -m pytest tests/test_rule_coverage_manifest.py -q -p no:cacheprovider
echo ALLDONE > $E/gate_${T}_DONE.txt
