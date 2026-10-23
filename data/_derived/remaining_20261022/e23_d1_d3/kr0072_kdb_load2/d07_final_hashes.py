# -*- coding: utf-8 -*-
"""read-only: final state of the files this load changed (sha256, bytes) next to the pre-load backup; and the check that the eight applier files still carry the post-apply hashes of the manifest
(= `e23_apply.py --revert --apply` stays valid after all tests ran)."""
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
BK = HERE.parent / "backup_before_apply/kr0072_kdb_load2"
man = json.loads((HERE / "apply_manifest_e23_kdb.json").read_text(encoding="utf-8"))
FILES = list(man["after_sha256"]) + ["tests/fixtures/master_tables_golden.json", "tests/fixtures/builder_input_fingerprints.json", "data/_derived/qoq_warn.json", "data/_derived/pl_oci_vs_bs_aoci_warn.json"]
ok = True
lines = []
for rel in FILES:
    cur = (ROOT / rel).read_bytes()
    pre = (BK / rel).read_bytes()
    h = hashlib.sha256(cur).hexdigest()
    tag = ""
    if rel in man["after_sha256"]:
        same = h == man["after_sha256"][rel]
        ok = ok and same
        tag = f" | == manifest after_sha256: {same}"
    lines.append(f"{h} *{rel} | {len(cur)} bytes (pre-load {len(pre)} bytes, sha {hashlib.sha256(pre).hexdigest()[:12]}){tag}")
print("\n".join(lines))
print("revert path valid (applier files carry the post-apply hashes):", ok)
(HERE / "final_state_sha256.txt").write_text("\n".join(lines) + f"\nrevert path valid: {ok}\n", encoding="utf-8", newline="\n")
sys.exit(0 if ok else 1)
