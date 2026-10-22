import json, subprocess, io, re, sys
sys.path.insert(0, "data/_derived/remaining_20261022/v_oci")
import locate as L

out = io.open("data/_derived/remaining_20261022/v_oci/recompute.txt", "w", encoding="utf-8")


def P(*a):
    out.write(" ".join(str(x) for x in a) + "\n")


def master(from_head):
    if from_head:
        b = subprocess.run(["git", "show", "HEAD:PL_breakdown.json"], capture_output=True, check=True).stdout
        rows = json.loads(b.decode("utf-8"))
    else:
        rows = json.load(open("PL_breakdown.json", encoding="utf-8"))
    return {(r["항목번호"], r["공시분기"]): (r["값"], r["값_당분기"]) for r in rows if r["원보험사코드"] == "KR0073"}


MH, MC = master(True), master(False)
HEDGE = ("위험회피파생상품평가손익", "위험회피목적파생상품평가손익", "현금흐름위험회피")


def classify(lab):
    l = lab.replace(" ", "")
    if l == "기타포괄손익":
        return 25
    if "공정가치측정채무증권평가손익" in l or "공정가치측정금융자산관련손익" in l:
        return 26
    if l == "보험계약자산(부채)순금융손익":
        return 27
    if l == "재보험계약자산(부채)순금융손익":
        return 30
    if l in HEDGE:
        return 28
    if "지정지분증권평가손익" in l or "공정가치측정유가증권평가손익" in l or "공정가치측정지분증권평가손익" in l:
        return 29
    if "총포괄손익" in l:
        return 31
    if re.match(r"^(\(.\))?(당기|반기|분기)?순이익", l):
        return 24
    if l.startswith("당기손익으로재분류"):
        return "SUB"
    return "OTHER"


def extract(block, colsel):
    d = {}
    other = []
    for ln, cells in block["rows"]:
        lab = cells[0][0]
        v = colsel(cells[1:])
        if v is None:
            continue
        k = classify(lab)
        if k == "OTHER":
            other.append((ln, lab, v / 1e6))
            continue
        if k == "SUB":
            continue
        d[k] = d.get(k, 0.0) + v / 1e6
    d[32] = sum(x[2] for x in other)
    return d, other


def ctxcol(ok_fn):
    def f(vals):
        for body, ctx in vals:
            if ctx and ok_fn(ctx.split("_")[0]) and L.num(body) is not None:
                return L.num(body)
        return None
    return f


def poscol(i):
    def f(vals):
        nums = [L.num(b) for b, c in vals if L.num(b) is not None]
        return nums[i] if len(nums) > i else None
    return f


def sepblock(name, startline=None):
    bs = L.blocks(L.FILES[name])
    if startline is None:
        cand = [b for b in bs if b["nrows"] >= 12 and b["sep_ctx"]]
    else:
        cand = [b for b in bs if b["start"] <= startline <= b["end"]]
    assert len(cand) == 1, (name, [(b["start"], b["sep_ctx"], b["nrows"]) for b in bs])
    return cand[0]


SPEC = {
    "2024.4Q": dict(orig="ORIG_2024Q4", oc=ctxcol(lambda c: c.startswith("CFY2024")), late="LATE_FY2025ann",
                    lc=ctxcol(lambda c: c.startswith("PFY2024")), l3=None, ls=None),
    "2025.1Q": dict(orig="ORIG_2025Q1", oc=ctxcol(lambda c: c in ("CFY2025dFQA","CFY2025eFQA")), late="LATE_FY2026Q1",
                    lc=ctxcol(lambda c: c in ("PFY2025dFQA","PFY2025eFQA")), l3=ctxcol(lambda c: c in ("PFY2025dFQQ","PFY2025eFQQ")), ls=None),
    "2025.2Q": dict(orig="ORIG_2025Q2", oc=ctxcol(lambda c: c in ("CFY2025dHYA","CFY2025eHYA")), late="LATE_FY2026Q2",
                    lc=poscol(3), l3=poscol(2), ls=31649),
}
ok = True
nchk = 0


def chk(cond, msg):
    global ok, nchk
    nchk += 1
    P(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        ok = False


for q, s in SPEC.items():
    P("=" * 20, q)
    ob = sepblock(s["orig"])
    lb = sepblock(s["late"], s["ls"])
    od, oo = extract(ob, s["oc"])
    ld, lo = extract(lb, s["lc"])
    for nm, dd, oth, blk in (("ORIG", od, oo, ob), ("LATE", ld, lo, lb)):
        P(nm, "separate-statement block L%d-L%d" % (blk["start"], blk["end"]), {k: round(v, 6) for k, v in sorted(dd.items())})
        P(nm, "other leaf rows (lines)", [(a, b[:16], round(c, 6)) for a, b, c in oth])
        parts = sum(dd.get(k, 0.0) for k in (26, 27, 28, 29, 30, 32))
        chk(abs(dd[25] - parts) < 1e-5, "%s %s 25 = 26+27+28+29+30+32 residual %.9f" % (q, nm, dd[25] - parts))
        chk(abs(dd[31] - dd[24] - dd[25]) < 1e-5, "%s %s 31 = 24+25 residual %.9f" % (q, nm, dd[31] - dd[24] - dd[25]))
    chk(abs(od[24] - ld[24]) < 1e-6, "%s NI(24) original == latest (%.6f)" % (q, od[24]))
    for it in (24, 25, 26, 27, 28, 29, 30, 31, 32):
        mh = MH.get((it, q), (None, None))[0]
        mc = MC.get((it, q), (None, None))[0]
        o = od.get(it, 0.0)
        l = ld.get(it, 0.0)
        P("item %d orig_raw %.6f | HEAD %s | latest_raw %.6f | CUR %s" % (it, o, mh, l, mc))
        chk((mh is None and abs(o) < 1e-6) or (mh is not None and abs(mh - o) < 1e-5), "%s item %d HEAD master == ORIGINAL filing current column" % (q, it))
        chk((mc is None and abs(l) < 1e-6) or (mc is not None and abs(mc - l) < 1e-5), "%s item %d CUR master == LATEST filing prior column" % (q, it))
    if s["l3"]:
        l3d, _ = extract(lb, s["l3"])
        P("latest filing printed 3M col", {k: round(v, 6) for k, v in sorted(l3d.items())})
        for it in (25, 26, 29, 31, 32):
            mc = MC.get((it, q), (None, None))[1]
            chk(mc is not None and abs(mc - l3d.get(it, 0.0)) < 1e-5, "%s item %d CUR 값_당분기 (%s) == printed 3M (%.6f)" % (q, it, mc, l3d.get(it, 0.0)))

# 2025.2Q single == cum2Q - cum1Q
for it in (25, 26, 29, 31, 32):
    c1 = MC[(it, "2025.1Q")][0] or 0.0
    d = MC[(it, "2025.2Q")][0] - c1
    chk(abs(d - MC[(it, "2025.2Q")][1]) < 1e-5, "2025.2Q item %d 값_당분기 == cum2Q - cum1Q (%.6f)" % (it, d))

# 2025.3Q
b3 = sepblock("ORIG_2025Q3")
ctxs = sorted(set(c.split("_")[0] for r in b3["rows"] for b, c in r[1][1:] if c))
P("ORIG_2025Q3 contexts", ctxs)
cum = [c for c in ctxs if c.startswith("CFY2025") and c.endswith("A")][0]
q3 = [c for c in ctxs if c.startswith("CFY2025") and c.endswith("Q")][0]
d9, _ = extract(b3, ctxcol(lambda c: c == cum))
d3, _ = extract(b3, ctxcol(lambda c: c == q3))
P("3Q 9M", {k: round(v, 6) for k, v in sorted(d9.items())})
P("3Q 3M", {k: round(v, 6) for k, v in sorted(d3.items())})
for it in (25, 26, 29, 31, 32):
    h, c = MH.get((it, "2025.3Q")), MC.get((it, "2025.3Q"))
    P("3Q item", it, "HEAD val/dangi", h, "CUR val/dangi", c, "printed 9M %.6f printed 3M %.6f" % (d9.get(it, 0.0), d3.get(it, 0.0)))
    chk(c[0] is not None and abs(c[0] - d9.get(it, 0.0)) < 1e-5, "2025.3Q item %d 값 unchanged == original 9M" % it)
chk(abs(MC[(29, "2025.3Q")][1] - d3[29]) < 1e-5, "2025.3Q item 29 값_당분기 (%.6f) == printed 3M in original Q3 filing (%.6f)" % (MC[(29, "2025.3Q")][1], d3[29]))
chk(abs(MC[(29, "2025.3Q")][1] - (MC[(29, "2025.3Q")][0] - MC[(29, "2025.2Q")][0])) < 1e-5, "2025.3Q item 29 dangi == cum3Q - cum2Q")
for it in (25, 26, 31, 32):
    chk(MC[(it, "2025.3Q")][1] is None and MC[(it, "2024.4Q")][1] is None, "item %d 2025.3Q and 2024.4Q 값_당분기 blank" % it)
    h3 = MH[(it, "2025.3Q")][1]
    P("  note: HEAD 2025.3Q item %d dangi %.6f vs original-filing printed 3M %.6f (blanked in CUR)" % (it, h3, d3.get(it, 0.0)))

# unchanged items
bad = []
for it in [i for i in range(1, 25)] + [27, 28, 30]:
    for q in ("2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"):
        if MH.get((it, q)) != MC.get((it, q)):
            bad.append((it, q))
chk(not bad, "items 1-24, 27, 28, 30 (incl 1 보험손익, 6, 7, 17 투자손익, 24 당기순이익) identical HEAD vs CUR across 2023.4Q..2026.1Q; diffs=%s" % bad)

# CUR master closure
for q in ("2024.4Q", "2025.1Q", "2025.2Q"):
    g = lambda it: (MC[(it, q)][0] or 0.0)
    parts = g(26) + g(27) + g(28) + g(29) + g(30) + g(32)
    chk(abs(g(25) - parts) < 1e-5, "CUR master %s cum 25 = parts (resid %.9f)" % (q, g(25) - parts))
    chk(abs(g(31) - g(24) - g(25)) < 1e-5, "CUR master %s cum 31 = 24+25 (resid %.9f)" % (q, g(31) - g(24) - g(25)))
for q in ("2025.1Q", "2025.2Q"):
    g = lambda it: (MC[(it, q)][1] or 0.0)
    parts = g(26) + g(27) + g(28) + g(29) + g(30) + g(32)
    chk(abs(g(25) - parts) < 1e-5, "CUR master %s single 25 = parts (resid %.9f)" % (q, g(25) - parts))
    chk(abs(g(31) - g(24) - g(25)) < 1e-5, "CUR master %s single 31 = 24+25 (resid %.9f)" % (q, g(31) - g(24) - g(25)))
P("CHECKS", nchk, "OVERALL", "PASS" if ok else "FAIL")
out.close()
print("done", ok, nchk)
