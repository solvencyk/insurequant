"""Tier-1 (statement) PL cells: compare 'new' with the prior-period cumulative column of the filing's own statement table.
Basis (separate/consolidated) is decided by an anchor: the CURRENT-period column must reproduce the master's current-period values."""
import sys, os, csv, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_pl import *
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
rows_all = list(csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")))
T1 = {1, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32}
cells = [r for r in rows_all if r["master"] == "PL_breakdown" and r["kind"] == "latest_comparative" and int(r["item"]) in T1 and "포괄손익계산서" in r["source_ref"]]
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
def mval(code, q, it):
    r = master.get((code, q, it))
    try: return float(r["값"])
    except Exception: return None
def cur_q(q):  # prior quarter label -> filing's current quarter label
    y, n = q.split("."); return f"{int(y)+1}.{n}"
out = open(here + "/c1_tier1.txt", "w", encoding="utf-8")
res = csv.writer(open(here + "/c1_tier1.csv", "w", encoding="utf-8-sig", newline=""))
res.writerow(["code", "quarter", "item", "old", "new", "mine", "table", "col", "scale", "anchor", "verdict"])
groups = {}
for c in cells:
    rc = re.search(r"rcept (\d+) \((FY\d{4}_Q\d)\)", c["source_ref"])
    groups.setdefault((c["code"], c["quarter"], rc.group(1), rc.group(2)), []).append(c)
bad = 0; tot = 0
for (code, q, rc, fyq), cs in sorted(groups.items()):
    p = find_xml(code, fyq, rc)[0]
    tabs = [t for t in load_tables(p) if is_statement(t)]
    cq = cur_q(q)
    # anchor each candidate table
    best = []
    for t in tabs:
        rws = stmt_rows(t)
        for sc in (1e-6, 1e-3, 1.0):
            score = 0; n = 0
            for it in sorted(T1):
                mv = mval(code, cq, it)
                v = define_all(rws, it)
                if mv is None or not v: continue
                n += 1
                cur = v[-3] if len(v) >= 4 else (v[-2] if len(v) >= 2 else v[0])
                if abs(cur * sc - mv) <= max(0.0015, abs(mv) * 1e-9 if sc != 1.0 else 0.6): score += 1
            best.append((score, n, t, sc, rws))
    best.sort(key=lambda x: -x[0])
    out.write(f"===== {code} {q} filing {fyq} {rc}: tables={[(b[2]['idx'], b[0], b[1], b[3]) for b in best[:4]]}\n")
    if not best or best[0][0] < 3:
        out.write("   ANCHOR FAILED\n")
    for c in cs:
        it = int(c["item"]); new = float(c["new"]); tot += 1
        found = []
        for score, n, t, sc, rws in best[:3]:
            if score < 3: continue
            v = define_all(rws, it)
            if v: found.append((t["idx"], sc, v[-1] * sc, score))
        ok = [f for f in found if abs(f[2] - new) <= (0.0015 if f[1] != 1.0 else 0.6)]
        verdict = "MATCH" if ok else "MISMATCH"
        if not ok: bad += 1
        top = found[0] if found else None
        res.writerow([code, q, it, c["old"], c["new"], f"{top[2]:.6f}" if top else "", top[0] if top else "", "last(prior cum)", top[1] if top else "", top[3] if top else "", verdict])
        out.write(f"   i{it:<2} old={c['old']:>16} new={new:>16.6f} mine={[round(f[2],6) for f in found]} -> {verdict}\n")
out.write(f"\ncells {tot} mismatches {bad}\n")
