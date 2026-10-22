# -*- coding: utf-8 -*-
"""Final independent check of plan_KR0070.json against the LIVE masters and the cited XML lines (read-only)."""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = ROOT/"data/_derived/remaining_20261022/e19_latest_comparative"
plan = json.loads((HERE/"plan_KR0070.json").read_text(encoding="utf-8"))
rows = json.loads((ROOT/"PL_breakdown.json").read_text(encoding="utf-8"))
gold = json.loads((ROOT/"data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
M = {(r["항목번호"], r["공시분기"]): r for r in rows if r["원보험사코드"] == "KR0070"}
L = []; bad = 0
req = ["quarter","item","old","new","unit","xml_file","xml_line","second_source"]
for c in plan["cells"]:
    miss = [k for k in req if k not in c or c[k] is None]
    if miss: bad += 1; L.append(f"MISSING FIELDS {c['quarter']} i{c['item']} {miss}")
    live = M[(c["item"], c["quarter"])]["값"]
    if abs(live - c["old"]) > 1e-6: bad += 1; L.append(f"OLD != live master {c['quarter']} i{c['item']} {live} vs {c['old']}")
# gold overlap
gk = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in gold["set"] if e["원보험사코드"] == "KR0070"}
L.append("gold set keys KR0070: " + str(sorted(gk)))
for c in plan["cells"]:
    if ("KR0070", c["item"], c["quarter"]) in gk: bad += 1; L.append("GOLD OVERLAP " + str(c["quarter"]) + str(c["item"]))
dn = [x for x in gold["null_dangi"]["cells"] if x[0] == "KR0070"]; ds = [x for x in gold["set_dangi"]["cells"] if x[0] == "KR0070"]
L.append(f"null_dangi KR0070 {dn} set_dangi KR0070 {ds}")
# independent XML reread of each cited line
def won(t):
    t = t.replace(",", "").strip(); neg = t.startswith("(") and t.endswith(")")
    return (-1 if neg else 1) * float(t.strip("()"))
cache = {}
for c in plan["cells"]:
    lines = cache.setdefault(c["xml_file"], (ROOT/c["xml_file"]).read_text(encoding="utf-8", errors="replace").split("\n"))
    tot = 0.0
    for p in c["xml_lines"]:
        txt = re.sub(r"<[^>]+>", "", lines[p["line"]-1]).strip()
        if txt != p["printed"]: bad += 1; L.append(f"TEXT MISMATCH {c['quarter']} i{c['item']} L{p['line']} {txt!r}")
        tot += p["sign"] * won(txt) / 1e6
    if abs(tot - c["new"]) > 2e-5: bad += 1; L.append(f"SUM MISMATCH {c['quarter']} i{c['item']} {tot} vs {c['new']}")
# merged closure from live master + adopted
adopt = {(c["quarter"], c["item"]): c["new"] for c in plan["cells"]}
def v(q, i):
    return adopt.get((q, i), M[(i, q)]["값"] if (i, q) in M else 0.0)
for q in ["2024.1Q","2024.2Q","2024.3Q"]:
    r = {
     "20=1+17": v(q,20)-v(q,1)-v(q,17),
     "22=20+21": v(q,22)-v(q,20)-v(q,21),
     "|22-24|=|23|": abs(v(q,22)-v(q,24))-abs(v(q,23)),
     "24=22-23": v(q,24)-(v(q,22)-v(q,23)),
     "31=24+25": v(q,31)-v(q,24)-v(q,25),
     "25=26+27+28+30+32": v(q,25)-sum(v(q,i) for i in (26,27,28,30,32)),
     "17=18+19": v(q,17)-v(q,18)-v(q,19),
     "bridge 1=2+13+14+15-16": v(q,1)-(v(q,2)+v(q,13)+v(q,14)+v(q,15)-v(q,16)),
    }
    for k, x in r.items():
        ok = abs(x) < 0.002
        if not ok: bad += 1
        L.append(f"{q} {k}: resid={x:.6f} {'ok' if ok else 'FAIL'}")
L.append(f"TOTAL problems {bad}")
(HERE/"KR0070_final_check.txt").write_text("\n".join(L)+"\n", encoding="utf-8")
print(bad)
