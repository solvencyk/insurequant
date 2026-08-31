# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "data" / "_derived" / "kics_transition_applicability.json"
d = json.loads(p.read_text(encoding="utf-8"))
data = d["records"]
quarters = sorted({r["quarter"] for r in data})
print("quarters covered:", quarters)
q2026_2 = [r for r in data if r["quarter"] == "2026.2Q"]
print("2026.2Q records:", len(q2026_2))
for r in q2026_2:
    print(r["code"], r["name"], "TFI=", r["TFI"])
