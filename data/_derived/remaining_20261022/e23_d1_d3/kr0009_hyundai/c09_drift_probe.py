# -*- coding: utf-8 -*-
"""read-only probe: KR0009 cells where a fresh build_pl() with the live gold differs from the live PL master (values + single quarters), and the CSM equivalent"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
import e23_apply as A
live = json.loads((A.ROOT / A.F["PL"]).read_text(encoding="utf-8"))
gold = json.loads((A.ROOT / A.F["GOLD"]).read_text(encoding="utf-8"))
base = A.simulate_rows(gold, "probe")
lb = {A.rkey(r): r for r in live}
bb = {A.rkey(r): r for r in base}
n = 0
for k in sorted((k for k in lb if k[0] == "KR0009"), key=lambda k: (k[2], int(k[1]))):
    if k[0] != "KR0009":
        continue
    a, b = lb[k], bb[k]
    if (a["값"], a.get("값_당분기")) != (b["값"], b.get("값_당분기")):
        n += 1
        print(k, "live", a["값"], a.get("값_당분기"), "| fresh build", b["값"], b.get("값_당분기"))
print("KR0009 PL drift cells:", n)
# all KR0009 live vs base for the planned cells
planned = sorted((c["item"], b["quarter"], c["old"]) for b in A.PLAN["buckets"] for c in b["cells"])
print("planned cells where live != fresh build 값:")
cnt = 0
for it, q, old in planned:
    k = ("KR0009", it, q)
    if not A.same(lb[k]["값"], bb[k]["값"]):
        cnt += 1
        print("   ", k, "live", lb[k]["값"], "fresh build", bb[k]["값"], "| dangi live", lb[k].get("값_당분기"), "fresh", bb[k].get("값_당분기"))
print("count", cnt, "of", len(planned))
