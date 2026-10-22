# -*- coding: utf-8 -*-
"""Final freshness check of plan_KR0032.json against the LIVE masters (read-only): old values, gold, dangi model, merged closure, seam list."""
import json
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
H = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
plan = json.loads((H / "plan_KR0032.json").read_text(encoding="utf-8"))
rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
kr = {(r["항목번호"], r["공시분기"]): r for r in rows if r["원보험사코드"] == "KR0032"}
out = []
bad = 0
for c in plan["cells"]:
    r = kr[(c["item"], c["quarter"])]
    ok = abs(r["값"] - c["old"]) < 1e-6
    bad += (not ok)
    out.append(f"{c['quarter']} i{c['item']} live={r['값']} plan.old={c['old']} ok={ok} dangi_live={r.get('값_당분기')}")
g = [e for e in gold["set"] if e["원보험사코드"] == "KR0032"]
out.append(f"gold set KR0032 in live gold file: {len(g)}")
for k in ("null_dangi", "set_dangi"):
    if k in gold:
        out.append(f"{k} KR0032: {[x for x in gold[k].get('cells', []) if x[0] == 'KR0032']}")
# merged closure per bucket with new values
def val(q, i, newmap):
    if (q, i) in newmap: return newmap[(q, i)]
    r = kr.get((i, q)); return None if r is None else r["값"]
newmap = {(c["quarter"], c["item"]): c["new"] for c in plan["cells"]}
for q in ("2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"):
    v = lambda i: val(q, i, newmap)
    chk = {
        "20=1+17": v(20) - (v(1) + v(17)),
        "|22-24|=|23|": abs(v(22) - v(24)) - abs(v(23)),
        "31=24+25": v(31) - (v(24) + v(25)),
        "17=18+19": v(17) - (v(18) + v(19)),
    }
    out.append(q + " merged closure resid " + json.dumps({k: round(x, 6) for k, x in chk.items()}))
# dangi model for all items in 2023.3Q..2024.4Q+2025.1Q after adoption
ytd_q = ["2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"]
seam = {(s["quarter"], s["item"]): s for s in plan["seam_cells"]}
nb = {(s["quarter"], s["item"]): s for s in plan["neighbour_effects"]}
out.append(f"plan seam_cells={len(seam)} neighbour_effects={len(nb)} auto_follow={len(plan['auto_follow_cells'])}")
for i in (17, 19, 20, 22, 23, 24, 25, 27):
    for qi in range(1, len(ytd_q)):
        q, p = ytd_q[qi], ytd_q[qi - 1]
        cur, prv = val(q, i, newmap), val(p, i, newmap)
        cur0, prv0 = kr[(i, q)]["값"], kr[(i, p)]["값"]
        curn, prvn = (q, i) in newmap, (p, i) in newmap
        mixed = curn != prvn
        d_new = None if (cur is None or prv is None) else round(cur - prv, 6)
        d_old = round(cur0 - prv0, 6)
        live_d = kr[(i, q)].get("값_당분기")
        out.append(f"i{i} {q}: live_dangi={live_d} old_diff={d_old} after_diff={d_new} operands_new=({prvn},{curn}) mixed={mixed} in_seam={(q,i) in seam} in_nb={(q,i) in nb}")
        if mixed and (q, i) not in seam and (q, i) not in nb:
            bad += 1
            out.append("   MISSING seam/neighbour entry")
out.append(f"BAD={bad}")
(H / "KR0032_s5_fresh.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("bad", bad)
