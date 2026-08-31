# -*- coding: utf-8 -*-
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

with open(ROOT / "data" / "_derived" / "kics_transition_applicability.json", encoding="utf-8") as f:
    d = json.load(f)

records = d.get("records")
print(type(records), len(records) if hasattr(records, "__len__") else "?")
if isinstance(records, list):
    for r in records:
        if r.get("원보험사코드") == "KR0005" and r.get("공시분기") in ("2026.1Q", "2026.2Q"):
            print(r)
elif isinstance(records, dict):
    for k, v in records.items():
        if "KR0005" in str(k):
            print(k, "->", v)
