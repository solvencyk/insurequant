#!/bin/bash
# fresh baseline on the LIVE files, then the candidate run with every candidate file served (gate_overlay drops all repo writes)
HERE="$(cd "$(dirname "$0")" && pwd)"
E="$HERE/../kyobo_csm_basis_fix_20261021"
S="$HERE/sim"
P="$E/R_nopins_package"
"$HERE/run_gates.sh" gates_pre_PL > "$HERE/gates_pre_PL_run.log" 2>&1
"$HERE/run_gates.sh" gates_sim_PL_R \
  CSM_waterfall.json="$P/CSM_waterfall.json" \
  data/_gold/user_csm_cells.json="$P/data/_gold/user_csm_cells.json" \
  data/_gold/gold_overlay_ledger.json="$P/data/_gold/gold_overlay_ledger.json" \
  CSM_waterfall_provenance.json="$P/CSM_waterfall_provenance.json" \
  PL_breakdown.json="$S/cand_pl.json" \
  data/_gold/user_pl_cells.json="$S/gold_pl_cand.json" \
  PL_breakdown_provenance.json="$S/prov_pl_cand.json" > "$HERE/gates_sim_PL_R_run.log" 2>&1
echo BOTH_DONE > "$HERE/run_both.done"
