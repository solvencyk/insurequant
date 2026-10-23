# -*- coding: utf-8 -*-
"""read-only: the --out-dir simulation files vs the files --apply wrote (manifest after_sha256) -> byte-identical?"""
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
SIM = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e23_kr0072_load2_sim")
man = json.loads((HERE / "apply_manifest_e23_kdb.json").read_text(encoding="utf-8"))
ok = True
for rel, h in man["after_sha256"].items():
    s = hashlib.sha256((SIM / rel).read_bytes()).hexdigest()
    ok = ok and s == h
    print(("SAME " if s == h else "DIFF ") + rel)
print("sim == applied:", ok)
