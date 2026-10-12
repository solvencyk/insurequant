import sys, os, csv, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_pl import *
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
cells = [r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["kind"] == "3m_as_cumulative"]
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
out = open(here + "/d1_3m_final.txt", "w", encoding="utf-8")
res = csv.writer(open(here + "/d1_3m_final.csv", "w", encoding="utf-8-sig", newline=""))
res.writerow(["code", "item", "old", "new", "printed_3m(cur)", "printed_cum(cur)", "Q1 master", "Q1+3m", "cum - (Q1+3m)", "verdict"])
for c in cells:
    code, it = c["code"], int(c["item"]); new = float(c["new"]); old = float(c["old"])
    rc = re.search(r"rcept (\d+)", c["source_ref"]).group(1)
    p = find_xml(code, "FY2023_Q2", rc)[0]
    tabs = [t for t in load_tables(p) if is_statement(t)]
    q1 = master.get((code, "2023.1Q", it)); q1v = float(q1["값"]) if q1 and q1.get("값") not in (None, "") else None
    hit = None
    for t in tabs:
        v = define_all(stmt_rows(t), it)
        if not v: continue
        for sc in (1e-6, 1e-3, 1.0):
            vv = [x * sc for x in v]
            for k, x in enumerate(vv):
                if abs(x - new) <= (0.0015 if sc != 1.0 else 0.6) and k >= 1:
                    # the previous printed value is the 3-month column of the same period
                    hit = (t["idx"], sc, k, vv[k - 1], x, vv); break
            if hit: break
        if hit: break
    if not hit:
        out.write(f"{code} item{it}: no statement column equals new {new}\n"); res.writerow([code, it, old, new, "", "", q1v, "", "", "NOT FOUND"]); continue
    idx, sc, k, m3, cum, vv = hit
    q1p3 = (q1v + m3) if q1v is not None else None
    resid = (cum - q1p3) if q1p3 is not None else None
    old_is_3m = abs(m3 - old) <= (0.0015 if sc != 1.0 else 0.6)
    verdict = "OK" if (old_is_3m and (resid is None or abs(resid) <= 1.0)) else ("OK(old=3m; Q1 master inconsistent)" if old_is_3m else "CHECK")
    out.write(f"{code} item{it} {c['item_name']}: table{idx} col{k} 3m={m3:.6f} cum={cum:.6f} | old={old} (old==3m: {old_is_3m}) Q1master={q1v} Q1+3m={q1p3} resid={resid} -> {verdict}\n")
    res.writerow([code, it, old, new, f"{m3:.6f}", f"{cum:.6f}", q1v, q1p3, resid, verdict])
