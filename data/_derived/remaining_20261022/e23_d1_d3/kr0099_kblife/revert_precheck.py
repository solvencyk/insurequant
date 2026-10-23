# -*- coding: utf-8 -*-
"""KR0099: would `e23_apply.py --revert --apply` work right now?  (the live files must still carry the post-apply sha256 of the manifest); read-only"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
MAN = json.loads((ROOT / "data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife/apply_manifest_e23_kblife.json").read_text(encoding="utf-8"))
sys.stdout.reconfigure(encoding="utf-8")
ok = True
for rel, h in MAN["after_sha256"].items():
    cur = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    ok = ok and cur == h
    print(f"{rel}: live sha256 == post-apply manifest {cur == h}")
print("REVERT POSSIBLE" if ok else "REVERT BLOCKED (a file moved after the apply)")
