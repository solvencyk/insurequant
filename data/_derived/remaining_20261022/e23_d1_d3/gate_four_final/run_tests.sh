#!/bin/bash
# usage: run_tests.sh   (strictly sequential; backs up the in-place builder outputs first and checks them after)
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
R=C:/Users/sangwook.cho/Desktop/insurequant
O=$R/data/_derived/remaining_20261022/e23_d1_d3/gate_four_final/tests
BK=$R/data/_derived/remaining_20261022/e23_d1_d3/gate_four_final/backup_inplace
mkdir -p $O $BK
FILES="data/dart/viz/csm_waterfall.json data/dart/viz/csm_amort_schedule.json data/dart/viz/insurance_pl_breakdown.json data/dart/viz/bs_snapshot.json data/dart/viz/sensitivity_heatmap.json data/dart/viz/pl_breakdown_master.json data/_derived/pl_breakdown_coverage.json PL_breakdown.json CSM_waterfall.json"
for f in $FILES; do mkdir -p "$BK/$(dirname $f)"; cp -p "$R/$f" "$BK/$f"; done
(cd $R && sha256sum $FILES) > $O/sha_before.txt
for t in test_rule_coverage_manifest test_gold_overlay_survives_rebuild test_identity_registry test_identity_tautology test_master_tables_golden test_viz_ifrs17_panels_golden test_viz_csm_waterfall_golden test_deploy_assets test_push_gate_wiring test_golden_input_fingerprint; do
  echo "[$(date +%H:%M:%S)] start $t"
  "$PY" -m pytest $R/tests/$t.py -q --no-header -p no:cacheprovider --rootdir=$R < /dev/null > $O/$t.txt 2>&1
  echo "[$(date +%H:%M:%S)] done $t rc=$?"
done
echo "[$(date +%H:%M:%S)] start fingerprints"
(cd $R && "$PY" scripts/validate_golden_input_fingerprints.py < /dev/null > $O/validate_golden_input_fingerprints.txt 2>&1); echo "[$(date +%H:%M:%S)] done fingerprints rc=$?"
echo "[$(date +%H:%M:%S)] start pl_golden"
(cd $R && RUN_PL_GOLDEN=1 "$PY" -m pytest tests/test_pl_breakdown_golden.py -q --no-header -p no:cacheprovider < /dev/null > $O/test_pl_breakdown_golden.txt 2>&1); echo "[$(date +%H:%M:%S)] done pl_golden rc=$?"
(cd $R && sha256sum $FILES) > $O/sha_after.txt
diff $O/sha_before.txt $O/sha_after.txt && echo "INPLACE_OUTPUTS_UNCHANGED"
echo ALLDONE
