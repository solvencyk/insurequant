# -*- coding: utf-8 -*-
"""read-only: how earlier chain steps recorded a REPLACED owner-gold entry (was / note) -> the ABL replacement follows the same convention"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
g = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
want = [("KR0003", 19, "2023.2Q"), ("KR0068", 20, "2023.1Q"), ("KR0070", 4, "2023.1Q")]
for e in g["set"]:
    k = (e["원보험사코드"], e["항목번호"], e["공시분기"])
    if k in want:
        print(k, "값", e["값"], "was", e.get("was"))
        print("   note:", str(e.get("note"))[:700])
