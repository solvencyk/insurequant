#!/bin/bash
# usage: run_gates_sim.sh <outdir-name> <simdir>   -- runs every gate once, one after another, serving the candidate files of <simdir> (gate_overlay.py drops all repo writes)
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"; SIM="$2"
mkdir -p "$HERE/$OUT"
MAPS=""
for rel in CSM_waterfall.json PL_breakdown.json IFRS17_BS.json PL_breakdown_provenance.json CSM_waterfall_provenance.json data/_gold/user_pl_cells.json data/_gold/user_csm_cells.json data/dart/viz/bs_manual_overrides.json data/_gold/pl_bridge_baseline.json data/_gold/csm_amort_identity_ledger.json; do
  if [ -f "$SIM/$rel" ]; then MAPS="$MAPS $rel=$SIM/$rel"; fi
done
echo "maps:$MAPS"
for g in master_tables data_contract csm_continuity ilp_portfolio ilp_lic nb_csm csm_waterfall csm_coverage; do
  echo "[$(date +%H:%M:%S)] start $g"
  "$PY" "$HERE/gate_overlay.py" $g "$HERE/$OUT/$g.txt" $MAPS > "$HERE/$OUT/$g.log" 2>&1
  echo "[$(date +%H:%M:%S)] done $g rc=$?"
done
echo ALLDONE
