# -*- coding: utf-8 -*-
"""KR0003: the backups under backup_before_apply/kr0003_lotte equal (a) the sha256 recorded in this load's manifest before_sha256 and (b) the KB라이프 manifest after_sha256 (= the chain state right before this load);
the extra/ fixtures equal extra_SHA256_preload.txt.  Also prints whether git HEAD differs (it does: the KB라이프 load of this chain is inside the pre-load state, so the backups are NOT git HEAD)."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0003_lotte"
HERE = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/kr0003_lotte"
MAN = json.loads((HERE / "apply_manifest_e23_lotte.json").read_text(encoding="utf-8"))
KB = json.loads((ROOT / "data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife/apply_manifest_e23_kblife.json").read_text(encoding="utf-8"))
sys.stdout.reconfigure(encoding="utf-8")
ok = True
for rel, h in MAN["before_sha256"].items():
    b = hashlib.sha256((BK / rel).read_bytes()).hexdigest()
    a = b == h
    c = b == KB["after_sha256"][rel]
    ok = ok and a and c
    print(f"{rel}: backup sha256 == this manifest before_sha256 {a}; == KB라이프 manifest after_sha256 {c}")
for line in (BK / "extra_SHA256_preload.txt").read_text(encoding="utf-8").splitlines():
    h, _, rel = line.partition(" *")
    b = hashlib.sha256((BK / rel).read_bytes()).hexdigest()
    ok = ok and (b == h)
    print(f"extra/{rel}: backup sha256 == preload list {b == h}")
print("ALL OK" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
