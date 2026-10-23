#!/bin/bash
# usage: run_gates.sh <outdir>   (strictly sequential; gate_overlay.py drops repo writes outside this folder)
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"; shift
mkdir -p "$HERE/$OUT"
for g in master_tables data_contract csm_continuity; do
  echo "[$(date +%H:%M:%S)] start $g"
  "$PY" "$HERE/gate_overlay.py" $g "$HERE/$OUT/$g.txt" "$@" < /dev/null > "$HERE/$OUT/$g.log" 2>&1
  echo "[$(date +%H:%M:%S)] done $g rc=$?"
done
echo ALLDONE
