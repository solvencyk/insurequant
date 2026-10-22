"""life_cands: candidate PL cells (latest comparative) for LIFE buckets whose legs follow the income-statement lines (Tier-1 only reader).
usage: life_cands.py KR0083:2024.4Q,KR0104:2023.1Q,...   -> life_cands_<code>_<q>.json/.txt (+ combined life_cands_all.json)
t2 note items (4,5,6,9,10,11) stay at the live master (override via tier2_override.json if present).  READ-ONLY."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import cand as K  # noqa: E402
import mlib as M  # noqa: E402
import plan_lib as PL  # noqa: E402
import stmtlib as S  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
pl, names, inames = M.load_pl()
gold = M.jload(M.SNAP / "user_pl_cells.json")
gold_cells = {(c["원보험사코드"], c["공시분기"], c["항목번호"]): c for c in gold["set"]}
allres = {}
spec = sys.argv[1].split(",")
for sp in spec:
    code, q = sp.split(":")
    m = pl[(code, q)]
    zf = None if m.get(6) is not None else frozenset()
    v, t1 = K.vector(code, q, "prior", zero_fill_ok=zf)
    if v is None:
        print(code, q, "no prior FS-API")
        continue
    ch = PL.changed(code, q, v, pl)
    clo = PL.closure(v)
    fy = M.later_fy(q)
    path = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
    lines = M.read_lines(path)
    tabs = S.statement_tables(lines)
    cites = {}
    if tabs:
        tb = tabs[0]
        for it, old, new in ch:
            hits = PL.cite_statement(lines, tb, new)
            hits = [h for h in hits if h[4] == h[5] - 1] or hits         # prior-YTD = last cell
            cites[it] = [(h[0][:30], h[1], h[2]) for h in hits[:2]]
    goldhit = {it: gold_cells[(code, q, it)] for it, _o, _n in ch if (code, q, it) in gold_cells}
    rec = {"code": code, "q": q, "later_filing": M.rel(path), "statement_table": [tabs[0]["start"], tabs[0]["end"]] if tabs else None,
           "cells": [{"item": it, "old": old, "new": new, "cite": cites.get(it), "gold": (goldhit[it].get("값") if it in goldhit else None),
                      "gold_was": (goldhit[it].get("was") if it in goldhit else None)} for it, old, new in ch],
           "closure": clo, "screen_eok": PL.screen_eok(code, q, v, pl), "n_cells": len(ch), "vector": {str(k): v.get(k) for k in range(1, 33)}}
    allres[f"{code}|{q}"] = rec
    lines_out = [f"=== {code} {names.get(code)} {q}  later filing {M.rel(path)}  stmt L{rec['statement_table']}  cells={len(ch)}",
                 "   closure: " + "; ".join(f"{k}={('%.4f' % x) if x is not None else None}" for k, x in clo.items()),
                 "   screen(억원 old,new,delta): " + json.dumps(rec["screen_eok"], ensure_ascii=False)]
    for c in rec["cells"]:
        gtxt = f" GOLD={c['gold']} (was {c['gold_was']})" if c["gold"] is not None else ""
        lines_out.append(f"   item {c['item']:>2} {inames.get(c['item'], '')[:20]:<20} old={c['old']!s:>16} new={c['new']:>18,.6f}{gtxt}  cite={c['cite']}")
    M.MEASURE.joinpath(f"life_cands_{code}_{q}.txt").write_text("\n".join(lines_out), encoding="utf-8")
    print("\n".join(lines_out)[:6000])
M.MEASURE.joinpath("life_cands_" + "_".join(s.replace(":", "-") for s in spec)[:80] + ".json").write_text(json.dumps(allres, ensure_ascii=False, indent=1), encoding="utf-8")
