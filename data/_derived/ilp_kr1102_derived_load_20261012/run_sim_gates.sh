#!/bin/bash
# before (live files) / after (the two masters served from the dry-run candidates in sim/) under identical gate code, strictly sequential, one gate at a time
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
D=C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ilp_kr1102_derived_load_20261012
for g in ilp_portfolio ilp_lic continuity master_tables data_contract live_artifacts; do
  echo "== $g before $(date +%H:%M:%S)" >> $D/run_sim_gates.progress
  $PY $D/gate_overlay.py $g $D/gate_before_$g.txt live > $D/gate_before_$g.log 2>&1
  echo "== $g after  $(date +%H:%M:%S)" >> $D/run_sim_gates.progress
  $PY $D/gate_overlay.py $g $D/gate_after_$g.txt $D/sim_map.json > $D/gate_after_$g.log 2>&1
  echo "== $g done   $(date +%H:%M:%S)" >> $D/run_sim_gates.progress
done
echo done > $D/sim_gates_done.flag
