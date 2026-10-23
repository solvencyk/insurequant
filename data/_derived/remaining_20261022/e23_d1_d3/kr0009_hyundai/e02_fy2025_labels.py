# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kr0009_verify as V
sys.stdout.reconfigure(encoding="utf-8")
V.F["N5"] = "data/dart/FY2025_Q4/raw/KR0009_현대해상_20260312001448/20260312001448.xml"
S5 = V.Stmt("N5")
on = False
for r in S5.rows:
    t = r["cells"][0]["text"] if r["cells"] else ""
    if V.nspace(t) == "기타포괄손익":
        on = True
    if on:
        print("   ", repr(t), [c["text"] for c in r["cells"][1:]][:3])
    if V.nspace(t) == "총포괄손익":
        break
