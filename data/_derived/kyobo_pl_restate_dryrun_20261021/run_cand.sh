#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
E="$HERE/../kyobo_csm_basis_fix_20261021"
S="$HERE/sim"
P="$E/R_nopins_package"
OUT="${1:-gates_sim_PL_R2}"
PROV="${2:-$S/prov_pl_cand.json}"
rm -f "$HERE/run_cand.done"
"$HERE/run_gates.sh" "$OUT" \
  CSM_waterfall.json="$P/CSM_waterfall.json" \
  data/_gold/user_csm_cells.json="$P/data/_gold/user_csm_cells.json" \
  data/_gold/gold_overlay_ledger.json="$P/data/_gold/gold_overlay_ledger.json" \
  CSM_waterfall_provenance.json="$P/CSM_waterfall_provenance.json" \
  PL_breakdown.json="$S/cand_pl.json" \
  data/_gold/user_pl_cells.json="$S/gold_pl_cand.json" \
  PL_breakdown_provenance.json="$PROV" > "$HERE/${OUT}_run.log" 2>&1
echo CAND_DONE > "$HERE/run_cand.done"
