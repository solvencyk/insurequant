#!/bin/bash
# usage: run_gates.sh <outdir>   (gates run strictly one after another; gate_overlay.py drops every repo write outside this folder)
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"
mkdir -p "$HERE/$OUT"
for g in master_tables data_contract csm_continuity ilp_portfolio ilp_lic nb_csm csm_waterfall csm_coverage; do
  echo "[$(date +%H:%M:%S)] start $g"
  "$PY" "$HERE/gate_overlay.py" $g "$HERE/$OUT/$g.txt" > "$HERE/$OUT/$g.log" 2>&1
  echo "[$(date +%H:%M:%S)] done $g rc=$?"
done
echo "[$(date +%H:%M:%S)] start xlsx_drift"
"$PY" "$HERE/../../../scripts/check_master_xlsx_drift.py" > "$HERE/$OUT/xlsx_drift.txt" 2>&1
echo "[$(date +%H:%M:%S)] done xlsx_drift rc=$?"
echo ALLDONE
