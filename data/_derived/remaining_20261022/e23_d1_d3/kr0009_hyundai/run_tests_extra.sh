#!/bin/bash
# usage: run_tests_extra.sh <tag>  -- the other tests that read the changed masters / gold files / provenance sidecars (strictly sequential)
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
cd C:/Users/sangwook.cho/Desktop/insurequant
O=data/_derived/remaining_20261022/e23_d1_d3/kr0009_hyundai
T=$1
for t in test_csm_continuity_exception test_pl_fs_note_lineage test_pl_reinsurer_disclosure_lineage test_pl_source_absent_exemption test_pl_source_absent_site_rolled_off test_prepush_scope test_push_gate_wiring; do
  S=$(date +%H:%M:%S)
  "$PY" -m pytest tests/$t.py -q --no-header -p no:cacheprovider < /dev/null > $O/pytest_${t}_$T.txt 2>&1
  RC=$?
  echo "[$S -> $(date +%H:%M:%S)] $t rc=$RC : $(tail -1 $O/pytest_${t}_$T.txt)"
done
echo ALLDONE
