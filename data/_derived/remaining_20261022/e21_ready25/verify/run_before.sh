#!/bin/bash
# HEAD bytes served (served files live in ./head/)
HERE="$(cd "$(dirname "$0")" && pwd)"
bash "$HERE/run_gates.sh" gates_before \
  PL_breakdown.json="$HERE/head/PL_breakdown.json" CSM_waterfall.json="$HERE/head/CSM_waterfall.json" \
  PL_breakdown_provenance.json="$HERE/head/PL_breakdown_provenance.json" CSM_waterfall_provenance.json="$HERE/head/CSM_waterfall_provenance.json" \
  data/_gold/user_pl_cells.json="$HERE/head/user_pl_cells.json" data/_gold/user_csm_cells.json="$HERE/head/user_csm_cells.json" \
  data/_gold/gold_overlay_ledger.json="$HERE/head/gold_overlay_ledger.json" data/dart/viz/pl_breakdown_master.json="$HERE/head/pl_breakdown_master.json"
