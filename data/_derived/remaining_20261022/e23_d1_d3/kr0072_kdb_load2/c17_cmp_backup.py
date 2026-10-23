# -*- coding: utf-8 -*-
"""read-only: compare every file of the pre-load backup (SHA256_preload.txt) with the live repo file."""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb_load2"
n_same = n_diff = 0
for line in (BK / "SHA256_preload.txt").read_text(encoding="utf-8").splitlines():
    h, _, rel = line.partition(" *")
    cur = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    same = cur == h
    n_same += same
    n_diff += (not same)
    print(("SAME " if same else "DIFF ") + rel)
print(f"same {n_same} diff {n_diff}")
sys.exit(0 if n_diff == 0 else 1)
