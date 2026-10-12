"""IFRS17_BS cells (65): prior-year-end column of the balance sheet in the NEXT annual report, basis decided by current-column anchor."""
import sys, os, csv, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_pl import *
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
cells = [r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["master"] == "IFRS17_BS"]
bs = {}
for r in json.load(open(REPO + "/IFRS17_BS.json", encoding="utf-8")):
    bs[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
def mval(code, q, it):
    r = bs.get((code, q, it))
    try: return float(r["값"])
    except Exception: return None
LAB = {1: [r"자산총계"], 2: [r"부채총계"], 3: [r"자본총계"], 4: [r"기타포괄손익누계액", r"기타포괄손익누계액\(손실\)", r"기타포괄손익누계액합계"],
       14: [r"재보험계약자산"], 20: [r"보험계약부채"], 31: [r"이익잉여금", r"이익잉여금\(결손금\)", r"이익잉여금\(손실\)", r"결손금", r"미처분이익잉여금"]}
def bs_vec(rows, it):
    for lab, vals, raw in rows:
        l = lab.replace(" ", "")
        for pat in LAB[it]:
            if re.fullmatch(pat, l) and len(vals) >= 2: return vals
    return None
def is_bs(t):
    labs = " ".join(strip_prefix(r[0]) if r else "" for r in t["rows"] if r)
    s = " ".join(x[0] for x in stmt_rows(t))
    return "자산총계" in s and "부채총계" in s and "자본총계" in s
out = open(here + "/e1_bs.txt", "w", encoding="utf-8")
res = csv.writer(open(here + "/e1_bs.csv", "w", encoding="utf-8-sig", newline=""))
res.writerow(["code", "quarter", "item", "old", "new", "mine", "table", "scale", "anchor", "verdict"])
groups = {}
for c in cells:
    m = re.search(r"rcept (\d+) \((FY\d{4}_Q\d)\)", c["source_ref"])
    groups.setdefault((c["code"], c["quarter"], m.group(1), m.group(2)), []).append(c)
bad = 0; tot = 0
for (code, q, rc, fyq), cs in sorted(groups.items()):
    p = find_xml(code, fyq, rc)[0]
    cq = f"{int(q[:4])+1}.{q[5:]}"
    cands = []
    for t in load_tables(p):
        if not is_bs(t): continue
        rows = stmt_rows(t)
        for sc in (1e-6, 1e-3, 1.0):
            score = 0; n = 0
            for it in LAB:
                v = bs_vec(rows, it); mv = mval(code, cq, it)
                if v is None or mv is None: continue
                n += 1
                tol = {1e-6: 0.001, 1e-3: 0.001, 1.0: 0.6}[sc]
                if abs(v[0] * sc - mv) <= tol: score += 1
            cands.append((score, n, t, sc, rows))
    cands.sort(key=lambda x: -x[0])
    out.write(f"===== {code} {q} {fyq} {rc}: top {[(c_[2]['idx'], c_[0], c_[1], c_[3]) for c_ in cands[:4]]}\n")
    for c in cs:
        it = int(c["item"]); new = float(c["new"]); tot += 1
        ok = None; mine = None; tinfo = None
        for score, n, t, sc, rows in cands[:3]:
            if score < 2: continue
            v = bs_vec(rows, it)
            if v is None: continue
            x = v[1] * sc
            tol = {1e-6: 0.0015, 1e-3: 0.0015, 1.0: 0.6}[sc]
            if mine is None: mine = x; tinfo = (t["idx"], sc, score)
            if abs(x - new) <= tol: ok = x; tinfo = (t["idx"], sc, score); break
        verdict = "MATCH" if ok is not None else "MISMATCH"
        if ok is None: bad += 1
        out.write(f"   i{it:<2} old={c['old']:>20} new={new:>20.6f} mine={mine} {tinfo} -> {verdict}\n")
        res.writerow([code, q, it, c["old"], c["new"], mine, tinfo[0] if tinfo else "", tinfo[1] if tinfo else "", tinfo[2] if tinfo else "", verdict])
out.write(f"\ncells {tot} mismatches {bad}\n")
