#!/bin/bash
# Extra push-hook domain gate (validate_live_artifacts reads PL_breakdown.json): baseline (live files) vs candidate (CSM R without pins + PL refresh).
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
E="$HERE/../kyobo_csm_basis_fix_20261021"
S="$HERE/sim"
P="$E/R_nopins_package"
rm -f "$HERE/run_live_artifacts.done"
echo "[$(date +%H:%M:%S)] baseline"
"$PY" "$HERE/gate_overlay.py" live_artifacts "$HERE/gates_pre_PL/live_artifacts.txt" > "$HERE/gates_pre_PL/live_artifacts.log" 2>&1
echo "[$(date +%H:%M:%S)] candidate"
"$PY" "$HERE/gate_overlay.py" live_artifacts "$HERE/gates_sim_PL_R2/live_artifacts.txt" \
  CSM_waterfall.json="$P/CSM_waterfall.json" \
  data/_gold/user_csm_cells.json="$P/data/_gold/user_csm_cells.json" \
  data/_gold/gold_overlay_ledger.json="$P/data/_gold/gold_overlay_ledger.json" \
  CSM_waterfall_provenance.json="$P/CSM_waterfall_provenance.json" \
  PL_breakdown.json="$S/cand_pl.json" \
  data/_gold/user_pl_cells.json="$S/gold_pl_cand.json" \
  PL_breakdown_provenance.json="$S/prov_pl_cand.json" > "$HERE/gates_sim_PL_R2/live_artifacts.log" 2>&1
echo "[$(date +%H:%M:%S)] done"
echo DONE > "$HERE/run_live_artifacts.done"
