#!/bin/bash
# k08: tests on the RESTORED live tree, strictly one after the other (RAM is tight).
# Before and after the tests the live files are hashed against the backup (k09) so any side effect is visible.
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
R="C:/Users/sangwook.cho/Desktop/insurequant"
E="$R/data/_derived/remaining_20261022/e23_d1_d3/kdb_restore"
cd "$R" || exit 9
"$PY" "$E/k09_hash_vs_backup.py" before-tests < /dev/null > /dev/null 2>&1; echo "[$(date +%H:%M:%S)] hash before-tests rc=$?"
for t in test_gold_overlay_survives_rebuild test_master_tables_golden test_rule_coverage_manifest; do
  echo "[$(date +%H:%M:%S)] start $t"
  "$PY" -m pytest tests/$t.py -q --no-header -p no:cacheprovider < /dev/null > "$E/pytest_${t}.txt" 2>&1
  echo "[$(date +%H:%M:%S)] done $t rc=$?"
  "$PY" "$E/k09_hash_vs_backup.py" "after-$t" < /dev/null > /dev/null 2>&1; echo "[$(date +%H:%M:%S)] hash after-$t rc=$?"
done
echo ALLDONE
