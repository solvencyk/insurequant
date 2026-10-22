#!/bin/bash
# usage: gates_scn.sh <scenario>   -- runs the 7 gates on cand/<scenario>_* (PL, PL provenance, CSM) served via gate_overlay, snapshot for everything else, then compares with g_base
SP="C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
HERE="$(cd "$(dirname "$0")" && pwd)"
S="$1"
CSM="$SP/cand/${S}_CSM_waterfall.json"; [ -f "$CSM" ] || CSM="$SP/snap/CSM_waterfall.json"
bash "$HERE/run_gates.sh" "g_$S" "PL_breakdown.json=$SP/cand/${S}_PL_breakdown.json" "PL_breakdown_provenance.json=$SP/cand/${S}_PL_breakdown_provenance.json" "CSM_waterfall.json=$CSM" "CSM_waterfall_provenance.json=$SP/snap/CSM_waterfall_provenance.json" "data/_gold/user_pl_cells.json=$SP/snap/user_pl_cells.json" "data/_gold/user_csm_cells.json=$SP/snap/user_csm_cells.json" 2>&1 | tail -2
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe "$HERE/compare_gates.py" g_base "g_$S" "$HERE/gates_compare_$S.txt" < /dev/null > /dev/null 2>&1
echo "compare written: gates_compare_$S.txt"
