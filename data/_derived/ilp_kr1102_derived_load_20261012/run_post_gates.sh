#!/bin/bash
# after the live write: the same gates on the LIVE files (overlay mode 'live': writes into the repository suppressed), strictly sequential
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
D=C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ilp_kr1102_derived_load_20261012
for g in ilp_portfolio ilp_lic continuity master_tables data_contract live_artifacts; do
  echo "== $g post $(date +%H:%M:%S)" >> $D/run_post_gates.progress
  $PY $D/gate_overlay.py $g $D/gate_post_$g.txt live > $D/gate_post_$g.log 2>&1
  echo "== $g done $(date +%H:%M:%S)" >> $D/run_post_gates.progress
done
echo done > $D/post_gates_done.flag
