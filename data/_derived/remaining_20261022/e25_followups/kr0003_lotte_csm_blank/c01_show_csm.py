# -*- coding: utf-8 -*-
"""READ-ONLY: live CSM_waterfall rows (값, 값_당분기) of KR0003 for 2023.1Q-2024.1Q, the CSM gold entries of KR0003, and builder-source (diag) values."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant"
live = {(r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{R}/CSM_waterfall.json", encoding="utf-8")) if r["원보험사코드"] == "KR0003"}
diag = {(r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{R}/data/dart/viz/csm_waterfall_master_diag.json", encoding="utf-8")) if r["원보험사코드"] == "KR0003"}
g = json.load(open(f"{R}/data/_gold/user_csm_cells.json", encoding="utf-8"))
gold = {(e["항목번호"], e["공시분기"]): e for e in g["set"] if e["원보험사코드"] == "KR0003"}
qs = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"]
print("item/name".ljust(22) + "".join(q.rjust(30) for q in qs))
for it in range(1, 7):
    cells = []
    for q in qs:
        r = live.get((it, q))
        d = diag.get((it, q))
        gv = gold.get((it, q))
        cells.append((f"{r['값']}/{r['값_당분기']}" if r else "-").rjust(22) + (" G" if gv else "  ") + (f"d{d['값']}" if d else "").ljust(6))
    print(f"{it} {str(live[(it, '2023.4Q')]['항목명'])[:16]:18s}" + "".join(c.rjust(30) for c in cells))
print("gold entries KR0003:", len(gold))
for k, e in sorted(gold.items(), key=lambda x: (x[0][1], x[0][0])):
    print("  ", k, "값", e["값"], "was", e["was"], "|", str(e.get("why"))[:160])
print("top-level keys of user_csm_cells.json:", list(g.keys()))
