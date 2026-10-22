#!/bin/bash
cd /c/Users/sangwook.cho/Desktop/insurequant
V=data/_derived/remaining_20261022/e20_held_and_remaining/verify
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
RUN_PL_GOLDEN=1 "$PY" -m pytest tests/test_pl_breakdown_golden.py -x -q -p no:cacheprovider < /dev/null > $V/pytest_pl_golden.txt 2>&1
echo "rc=$?" >> $V/pytest_pl_golden.txt
