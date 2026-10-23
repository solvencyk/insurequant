# -*- coding: utf-8 -*-
"""read-only: print the full plan cell JSON for chosen (quarter, item) pairs."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / "e23_plan_kdb.json").read_text(encoding="utf-8"))
want = {("2023.2Q", 3), ("2023.2Q", 7), ("2023.2Q", 12), ("2023.2Q", 15), ("2023.2Q", 18), ("2023.2Q", 19), ("2023.2Q", 32), ("2023.2Q", 4), ("2023.2Q", 2), ("2023.2Q", 8), ("2023.2Q", 26), ("2023.2Q", 29)}
for b in plan["buckets"]:
    for c in b["cells"]:
        if (b["quarter"], c["item"]) in want:
            d = dict(c)
            print(json.dumps(d, ensure_ascii=False, indent=1)[:3500])
            print("-----")
