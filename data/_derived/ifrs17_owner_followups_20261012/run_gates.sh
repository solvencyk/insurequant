#!/bin/bash
# before/after gate runs under identical gate code (baseline = backups of every master I changed), strictly sequential
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
D=C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_owner_followups_20261012
for g in ilp_portfolio ilp_lic continuity master_tables data_contract; do
  $PY $D/gate_overlay.py $g $D/gate_before_$g.txt $D/baseline_map.json > $D/gate_before_$g.log 2>&1
  $PY $D/gate_overlay.py $g $D/gate_after_$g.txt live > $D/gate_after_$g.log 2>&1
done
echo done > $D/gates_done.flag
