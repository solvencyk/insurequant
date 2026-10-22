import json
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
EV = ROOT + "data/_derived/remaining_20261022/e19_latest_comparative/"
plan = json.load(open(EV + "plan_KR0083.json", encoding="utf-8"))
pl = json.load(open(ROOT + "PL_breakdown.json", encoding="utf-8"))
rows = pl if isinstance(pl, list) else (pl.get("rows") or pl.get("data") or list(pl.values())[0])
M = {}
for r in rows:
    if r.get("원보험사코드") == "KR0083":
        M[(r["항목번호"], r["공시분기"])] = r
gold = json.load(open(ROOT + "data/_gold/user_pl_cells.json", encoding="utf-8"))
gs = gold.get("set", [])
gk = [(g["원보험사코드"], g["항목번호"], g["공시분기"]) for g in gs if g.get("원보험사코드") == "KR0083"]
gnd = [c for c in gold.get("null_dangi", {}).get("cells", []) if c[0] == "KR0083"]
gsd = [c for c in gold.get("set_dangi", {}).get("cells", []) if c[0] == "KR0083"]
out = open(EV + "KR0083_recheck2.txt", "w", encoding="utf-8")
W = lambda s: out.write(s + "\n")
W("gold set keys KR0083: %s" % sorted(gk, key=lambda x: (x[2], x[1])))
W("gold null_dangi KR0083: %s ; set_dangi KR0083: %s" % (gnd, gsd))
bad = 0
for c in plan["cells"]:
    r = M.get((c["item"], c["quarter"]))
    live = r["값"] if r else None
    ok = r is not None and abs(live - c["old"]) < 5e-7
    hit = ("KR0083", c["item"], c["quarter"]) in gk
    if not ok or hit: bad += 1
    W("live %s i%d master=%s plan_old=%s ok=%s gold_hit=%s" % (c["quarter"], c["item"], live, c["old"], ok, hit))
for s in plan["seam_cells"]:
    r = M.get((s["item"], s["quarter"]))
    live = r.get("값_당분기") if r else None
    ok = r is not None and abs(live - s["old"]) < 5e-7
    if not ok: bad += 1
    W("live seam %s i%d dangi=%s plan_old=%s ok=%s" % (s["quarter"], s["item"], live, s["old"], ok))
# 2024.4Q single unchanged check inputs
for it in (17, 19, 20, 22, 23, 24, 25, 27):
    a = M[(it, "2024.4Q")]; b = M[(it, "2024.3Q")]
    W("4Q i%d ytd4=%s ytd3=%s dangi4=%s derived=%s" % (it, a["값"], b["값"], a.get("값_당분기"), a["값"] - b["값"]))
# closure on merged vector, 2024.1Q and 2024.2Q
newv = {(c["quarter"], c["item"]): c["new"] for c in plan["cells"]}
def v(q, it):
    return newv.get((q, it), M[(it, q)]["값"] if (it, q) in M and M[(it, q)]["값"] is not None else 0.0)
for q in ("2024.1Q", "2024.2Q"):
    res = {
        "20=1+17": v(q, 20) - v(q, 1) - v(q, 17),
        "|22-24|=|23|": abs(v(q, 22) - v(q, 24)) - abs(v(q, 23)),
        "31=24+25": v(q, 31) - v(q, 24) - v(q, 25),
        "25=26+27+28+30+32": v(q, 25) - sum(v(q, i) for i in (26, 27, 28, 30, 32)),
        "17=18+19": v(q, 17) - v(q, 18) - v(q, 19),
        "22=20+21": v(q, 22) - v(q, 20) - v(q, 21),
        "1=2+13+14+15-16": v(q, 1) - (v(q, 2) + v(q, 13) + v(q, 14) + v(q, 15) - v(q, 16)),
    }
    W("closure %s %s" % (q, {k: round(x, 6) for k, x in res.items()}))
    if any(abs(x) > 0.002 for x in res.values()): bad += 1
W("BAD=%d" % bad)
