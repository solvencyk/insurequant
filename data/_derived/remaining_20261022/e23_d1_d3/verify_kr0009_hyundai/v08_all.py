import sys, json
sys.path.insert(0, ".")
import vlib9, vmaster
from vpl import read_col, items_from, H as PH, W as PW
CH, CW = vmaster.load_all("CSM_waterfall")
out = []
def P(s=""):
    print(s); out.append(s)
Q = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]
FY = {"2023.1Q": "FY2024_Q1", "2023.2Q": "FY2024_Q2", "2023.3Q": "FY2024_Q3", "2023.4Q": "FY2024_Q4"}
# ---- A. PL item 4 from 보험수익 note (장기 column, 보험계약마진상각 first row per table), prior-period tables
P("=== A. PL item 4 (원수 CSM상각) from 보험수익 note")
for q in Q:
    fy = FY[q]
    lines = vlib9.load(fy)
    sec = [i for i, ln in enumerate(lines, 1) if "<TITLE" in ln and "5. 재무제표 주석" in ln][0]
    T = vlib9.tables(fy)
    vals = []
    for ti, t in enumerate(T):
        if t["start"] < sec: continue
        hdr = [c[1] for c in t["rows"][0]["cells"]] if t["rows"] else []
        if hdr[:5] != ["구 분", "장기", "자동차", "일반", "합계"]: continue
        for r in t["rows"]:
            cs = r["cells"]
            if cs and cs[0][1] == "보험계약마진상각":
                vals.append((ti, r["line"], cs[1][1], cs[4][1])); break
    P("  %s %s tables(first 보험계약마진상각 row each): %s" % (q, fy, vals))
    pick = {"2023.1Q": 1, "2023.2Q": 2, "2023.3Q": 2}.get(q)
    if q == "2023.4Q":
        pick = None
    for k, v in enumerate(vals):
        pass
    w = PW[(q, 4)]["값"]; h = PH[(q, 4)]["값"]
    P("    master item4 HEAD %s WORK %s ; candidates(백만원) %s" % (h, w, [vlib9.num(v[2]) / 1e3 for v in vals]))
# ---- B. dangi recompute
P("\n=== B. 값_당분기 recompute from consecutive cumulative cells (same master vintage)")
nb = 0; nn = 0
for name, M in (("PL", PW), ("CSM", CW)):
    items = sorted(set(k[1] for k in M))
    for it in items:
        for qi, q in enumerate(Q):
            row = M.get((q, it))
            if not row: continue
            cum = row["값"]; dg = row["값_당분기"]
            if name == "PL":
                prev = M.get((Q[qi - 1], it))["값"] if qi else 0.0
                if qi and prev is None: exp = None
                else: exp = None if cum is None else (cum - (prev or 0.0))
            else:
                if it == 1:   # opening: prior quarter closing (cumulative item 6) or own cumulative opening in Q1
                    exp = row["값"] if qi == 0 else M.get((Q[qi - 1], 6))["값"]
                elif it == 6: exp = cum
                else:
                    prev = M.get((Q[qi - 1], it))["값"] if qi else 0.0
                    exp = None if cum is None else cum - prev
            nn += 1
            if q == "2023.4Q" and name == "PL" and dg is None:
                note = "null_dangi"
                ok = True
            else:
                ok = (exp is None and dg is None) or (exp is not None and dg is not None and abs(dg - exp) <= (0.0015 if name == "PL" else 0.0501))
                note = ""
            if not ok:
                nb += 1; P("  DANGI MISMATCH %s %s item %d: master %s expected %s" % (name, q, it, dg, exp))
P("dangi cells checked %d, mismatches %d" % (nn, nb))
# 4Q PL null_dangi cells list and what the formula would give
P("\n=== B2. 2023.4Q PL null_dangi")
nulls = [it for (q, it), r in sorted(PW.items()) if q == "2023.4Q" and r["값_당분기"] is None]
P("2023.4Q PL cells with null 값_당분기: %d items %s" % (len(nulls), nulls))
hnull = [it for (q, it), r in sorted(PH.items()) if q == "2023.4Q" and r["값_당분기"] is None]
P("  in HEAD: %d items %s" % (len(hnull), hnull))
for it in nulls:
    if PW[("2023.4Q", it)]["값"] is None: continue
# ---- C. printed 3-month prior column vs master dangi (seam)
P("\n=== C. printed prior-year 3-month column vs master 값_당분기 (PL, items readable from statement)")
def read3(fy):
    from v03_dump_stmt import sep_stmt
    (t, ti), = sep_stmt(fy)
    d = {}
    for r in t["rows"]:
        cs = r["cells"]
        if len(cs) >= 5 and cs[0][1] and cs[0][1] not in d:
            d[cs[0][1]] = (vlib9.num(cs[3][1]), r["line"])
    return {lab: (v, ln) for lab, (v, ln) in d.items()}
for q in ("2023.1Q", "2023.2Q", "2023.3Q"):
    d3 = read3(FY[q])
    # build a pseudo-dict with same signature as read_col: label->(value,line,raw)
    pd = {lab: (v, ln, "") for lab, (v, ln) in d3.items()}
    it3 = items_from(pd)
    bad = 0; n = 0
    for it, v in sorted(it3.items()):
        m = PW[(q, it)]["값_당분기"]
        n += 1
        if m is None or abs(m - v) > 0.0015:
            bad += 1; P("  %s item %d: master dangi %s vs printed 3-month %.6f" % (q, it, m, v))
    P("  %s: %d items compared, %d mismatches" % (q, n, bad))
# ---- D. original vintage (current column of FY2023 filings) vs master
P("\n=== D. original FY2023 filing current col vs HEAD vs WORK (Q3, Q4)")
for fy, q in (("FY2023_Q3", "2023.3Q"), ("FY2023_Q4", "2023.4Q")):
    from v03_dump_stmt import sep_stmt
    (t, ti), = sep_stmt(fy)
    rows = t["rows"]
    hdr = [c[1] for c in rows[0]["cells"]]
    ci = 2 if fy.endswith("Q3") else 1
    d = {}
    for r in rows:
        cs = r["cells"]
        if len(cs) > ci and cs[0][1] and cs[0][1] not in d:
            d[cs[0][1]] = (vlib9.num(cs[ci][1]), r["line"], cs[ci][1])
    it = items_from(d)
    dif = []
    for k, v in sorted(it.items()):
        w = PW[(q, k)]["值" if False else "값"]; h = PH[(q, k)]["값"]
        flag = "" if abs(v - w) <= 0.0015 else "  DIFF(orig vs WORK)"
        P("  %s item %2d orig %.6f HEAD %s WORK %s%s" % (q, k, v, h, w, flag))
open("v08_all.txt", "w", encoding="utf-8").write("\n".join(out))
