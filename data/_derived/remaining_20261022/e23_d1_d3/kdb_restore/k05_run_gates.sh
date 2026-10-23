#!/bin/bash
# k05: run the same seven read-only gates the KDB loader ran before its load (gate_overlay.py drops every
# repo write outside its own folder), against the RESTORED live tree; outputs go to gates_restored/.
# usage: k05_run_gates.sh   (strictly one gate after the other)
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
OVERLAY="$HERE/../kr0072_kdb_load2/gate_overlay.py"
OUT="$HERE/gates_restored"
mkdir -p "$OUT"
for g in master_tables data_contract csm_continuity csm_waterfall nb_csm csm_coverage live_artifacts; do
  echo "[$(date +%H:%M:%S)] start $g"
  "$PY" "$OVERLAY" $g "$OUT/$g.txt" < /dev/null > "$OUT/$g.log" 2>&1
  echo "[$(date +%H:%M:%S)] done $g rc=$?"
done
echo ALLDONE
