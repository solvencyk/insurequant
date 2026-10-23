# -*- coding: utf-8 -*-
"""KR0099: the backups under backup_before_apply/kr0099_kblife equal git HEAD (newline-normalised) and their sha256 equals the before_sha256 of the apply manifest."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0099_kblife"
MAN = json.loads((ROOT / "data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife/apply_manifest_e23_kblife.json").read_text(encoding="utf-8"))
sys.stdout.reconfigure(encoding="utf-8")
ok = True
for rel, h in MAN["before_sha256"].items():
    b = (BK / rel).read_bytes()
    head = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout
    same_head = b.replace(b"\r\n", b"\n") == head.replace(b"\r\n", b"\n")
    same_man = hashlib.sha256(b).hexdigest() == h
    ok = ok and same_head and same_man
    print(f"{rel}: backup == git HEAD (newline-normalised) {same_head}; sha256 == manifest before_sha256 {same_man}")
print("ALL OK" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
