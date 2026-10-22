#!/bin/bash
# usage: run_gates_exc.sh <scenario>  -- master_tables + csm_continuity only, with the SANDBOX WFY_EXCEPTIONS (KB라이프 2023, 롯데 2023 registered); output folder g_exc_<scenario>
SP="C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
S="$1"
CSM="$SP/cand/${S}_CSM_waterfall.json"; [ -f "$CSM" ] || CSM="$SP/snap/CSM_waterfall.json"
OUT="g_exc_$S"; mkdir -p "$HERE/$OUT"
ARGS=("PL_breakdown.json=$SP/cand/${S}_PL_breakdown.json" "PL_breakdown_provenance.json=$SP/cand/${S}_PL_breakdown_provenance.json" "CSM_waterfall.json=$CSM" "CSM_waterfall_provenance.json=$SP/snap/CSM_waterfall_provenance.json" "data/_gold/user_pl_cells.json=$SP/snap/user_pl_cells.json" "data/_gold/user_csm_cells.json=$SP/snap/user_csm_cells.json")
for g in master_tables csm_continuity; do
  echo "[$(date +%H:%M:%S)] start $g"
  "$PY" "$HERE/gate_overlay_exc.py" $g "$HERE/$OUT/$g.txt" "${ARGS[@]}" > "$HERE/$OUT/$g.log" 2>&1 < /dev/null
  echo "[$(date +%H:%M:%S)] done $g rc=$?"
done
echo ALLDONE
