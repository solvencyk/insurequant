#!/bin/bash
# k02: restore the 12 files the KDB (KR0072) load changed, byte for byte, from the pre-load backup.
# Guard: a file is overwritten only if its current bytes are still the post-load bytes saved in
# post_load_copies/ (otherwise somebody else touched it after the load and the script stops).
# Never regenerates anything; uses cp only (no redirect, so no BOM can be added).
R="C:/Users/sangwook.cho/Desktop/insurequant"
E="$R/data/_derived/remaining_20261022/e23_d1_d3"
BK="$E/backup_before_apply/kr0072_kdb_load2"
SNAP="$E/kr0072_kdb_load2/post_load_copies"
FILES="PL_breakdown.json CSM_waterfall.json PL_breakdown_provenance.json CSM_waterfall_provenance.json data/_gold/user_pl_cells.json data/_gold/user_csm_cells.json data/_gold/gold_overlay_ledger.json tests/test_rule_coverage_manifest.py tests/fixtures/master_tables_golden.json tests/fixtures/builder_input_fingerprints.json data/_derived/qoq_warn.json data/_derived/pl_oci_vs_bs_aoci_warn.json"

echo "[$(date +%H:%M:%S)] guard check"
for f in $FILES; do
  cur=$(sha256sum "$R/$f" | cut -c1-64)
  snap=$(sha256sum "$SNAP/$f" | cut -c1-64)
  if [ "$cur" != "$snap" ]; then
    echo "ABORT: $f differs from the post-load snapshot (cur $cur, snap $snap); nothing was changed"
    exit 1
  fi
done
echo "guard ok: all 12 current files are byte-identical to the post-load snapshot"

echo "[$(date +%H:%M:%S)] restore"
for f in $FILES; do
  cp "$BK/$f" "$R/$f" || { echo "FAILED to copy $f"; exit 2; }
  echo "restored $f"
done
echo "[$(date +%H:%M:%S)] done"
