# -*- coding: utf-8 -*-
"""read-only: sample of the gold entries written by this load (one new + one replaced entry per overlay) and the KR0072 set_dangi cells."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
pl = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
cs = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
k = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])  # noqa: E731
for name, g, wants in (("PL", pl, [("KR0072", 1, "2023.1Q"), ("KR0072", 4, "2023.2Q")]), ("CSM", cs, [("KR0072", 1, "2023.1Q"), ("KR0072", 4, "2023.1Q")])):
    for e in g["set"]:
        if k(e) in wants:
            print(f"== {name} gold {k(e)}: 값 {e['값']} was {e['was']}")
            print("   " + (e.get("note") or e.get("why"))[:1500])
print("== set_dangi KR0072 cells")
for c in pl["set_dangi"]["cells"]:
    if c[0] == "KR0072":
        print("  ", c[:4], str(c[4])[:260])
print("== gold KR0072 entries now: PL", sum(1 for e in pl["set"] if e["원보험사코드"] == "KR0072"), "CSM", sum(1 for e in cs["set"] if e["원보험사코드"] == "KR0072"))
