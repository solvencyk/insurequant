#!/bin/bash
cd /c/Users/sangwook.cho/Desktop/insurequant || exit 9
D=data/_derived/ifrs17_latest_comparative_apply_audit_20261013
T=artifacts/pytest_tmp/$(date +%Y%m%dT%H%M%S)_val
mkdir -p "$T"
export FULL_COVERAGE_SWEEP=1 PYTEST_DEBUG_TEMPROOT="$T"
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest -q -p no:cacheprovider $(tr '\n' ' ' < $D/m1_hooklist.txt) > $D/gates/hook_tests.txt 2>&1
echo "rc=$?" >> $D/gates/hook_tests.txt
