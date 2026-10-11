"""Revert the round-6 item-4 apply: restore PL_breakdown.json + PL_breakdown_provenance.json from my backup, but ONLY if the live files are still
byte-identical to what the loader wrote (load_manifest_item4.json hash_after) -- otherwise somebody else touched them and a cell-level removal of the
20 rows / 20 contract_notes blocks is needed instead.   usage: revert_item4_apply.py [--do]   (without --do: check only)"""
import hashlib, json, shutil, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[4]
B = ROOT / "data/_derived/bspl_apply_backup_20261011/item4_reinsurers"
M = json.loads((Path(__file__).with_name("load_manifest_item4.json")).read_text(encoding="utf-8"))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for n, h in M["hash_after"].items():
    live = sha(ROOT / n)
    print(n, "live", live[:12], "== loader output" if live == h else "!= loader output (changed since)")
    if live != h:
        raise SystemExit("ABORT: not reverting; remove the 20 rows / 20 blocks cell by cell instead")
    if sha(B / n) != M["hash_before"][n]:
        raise SystemExit(f"ABORT: backup {n} hash differs from recorded pre-apply hash")
if "--do" in sys.argv:
    for n in M["hash_after"]:
        shutil.copyfile(B / n, ROOT / n)
        assert sha(ROOT / n) == M["hash_before"][n]
        print("restored", n)
else:
    print("check only (pass --do to restore)")
