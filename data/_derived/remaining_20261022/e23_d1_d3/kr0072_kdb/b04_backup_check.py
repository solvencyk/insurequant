# -*- coding: utf-8 -*-
"""KR0072: (a) the backups under backup_before_apply/kr0072_kdb equal this load's manifest before_sha256 AND the ABL manifest after_sha256 (= the chain state right before this load) AND SHA256_preload.txt;
(b) the live files equal this load's manifest after_sha256 (the revert path is valid: e23_apply.py --revert --apply only works while the live files carry the post-apply hashes);
(c) lists which other files differ from SHA256_preload.txt (fixtures that tests update later)."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data/_derived/remaining_20261022/e23_d1_d3"
BK = EV / "backup_before_apply/kr0072_kdb"
MAN = json.loads((EV / "kr0072_kdb/apply_manifest_e23_kdb.json").read_text(encoding="utf-8"))
ABLM = json.loads((EV / "kr0070_abl/apply_manifest_e23_abl.json").read_text(encoding="utf-8"))
sys.stdout.reconfigure(encoding="utf-8")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


ok = True
pre = {}
for line in (BK / "SHA256_preload.txt").read_text(encoding="utf-8").splitlines():
    h, _, rel = line.partition(" *")
    pre[rel] = h
for rel, h in MAN["before_sha256"].items():
    b = sha(BK / rel)
    a, c, d = b == h, b == ABLM["after_sha256"].get(rel, b), b == pre[rel]
    ok = ok and a and c and d
    print(f"{rel}: backup == this manifest before_sha256 {a}; == ABL manifest after_sha256 {c}; == SHA256_preload {d}")
for rel, h in MAN["after_sha256"].items():
    cur = sha(ROOT / rel)
    ok = ok and cur == h
    print(f"{rel}: live == this manifest after_sha256 {cur == h}")
for rel, h in sorted(pre.items()):
    if rel in MAN["before_sha256"]:
        continue
    cur = sha(ROOT / rel)
    print(f"(not written by the applier) {rel}: live == preload {cur == h}")
print("ALL OK" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
