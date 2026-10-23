#!/bin/bash
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/gates"
for g in master_tables data_contract csm_continuity csm_waterfall nb_csm csm_coverage live_artifacts; do
  echo "[$(date +%H:%M:%S)] start $g"
  "$PY" "$HERE/gate_overlay.py" $g "$HERE/gates/$g.txt" < /dev/null > "$HERE/gates/$g.log" 2>&1
  echo "[$(date +%H:%M:%S)] done $g rc=$?"
done
echo ALLDONE
