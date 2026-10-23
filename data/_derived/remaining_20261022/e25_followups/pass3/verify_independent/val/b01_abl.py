# -*- coding: utf-8 -*-
"""Validation: ABL (KR0070) independent re-read of the 보험수익/보험서비스비용 notes, own filing columns."""
import json, sys, glob, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val")
from vtab import load_tables, num

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
FILINGS = {
    "2025.3Q": "data/dart/FY2025_Q3/raw/KR0070_에이비엘생명보험/20251114002593.xml",
    "2025.4Q": "data/dart/FY2025_Q4/raw/KR0070_에이비엘생명보험_20260331003080/20260331003080.xml",
    "2026.1Q": "data/dart/FY2026_Q1/raw/KR0070_에이비엘생명보험/xml/20260529000613.xml",
    "2026.2Q": "data/dart/FY2026_Q2/raw/KR0070_에이비엘생명보험/20260814003770.xml",
    # neighbors: prior-year columns of FY2026 filings
}
pl = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
M = {}
for r in pl:
    if r["원보험사코드"] == "KR0070":
        M[(r["공시분기"], str(r["항목번호"]))] = (r.get("값"), r.get("값_당분기"))


def sect_table(tabs, kind):
    out = []
    for s, e, rows in tabs:
        labs = [r[0] for r in rows if r]
        j = " ".join(labs)
        if kind == "rev" and "예상보험금" in j and "보험계약마진상각" in j and "재보험수익" in j and "예상계약유지비" in j:
            out.append((s, rows))
        if kind == "cost" and "발생보험금" in j and "보험계약마진상각" in j and "재보험비용" in j and "발생계약유지비" in j and "손실부담계약관련비용" in j:
            out.append((s, rows))
    return out


def split(rows, head, rhead):
    """split rows into insurance section and reinsurance section: dict label->[nums]"""
    sec = None
    A, B = {}, {}
    for r in rows:
        lab = r[0].replace(" ", "")
        nums = [num(c) for c in r[1:]]
        if lab == head:
            sec = A
            continue
        if lab == rhead:
            sec = B
            continue
        if lab in ("합계", "기타사업비용"):
            sec = None
            continue
        if sec is not None and all(n is not None for n in nums) and nums:
            key = lab
            if key in sec:
                key = key + "#2"
            sec[key] = nums
    return A, B


def col(d, lab, i):
    return d[lab][i]


def compute(rev_rows, cost_rows, i):
    rA, rB = split(rev_rows, "보험수익", "재보험수익")
    cA, cB = split(cost_rows, "보험서비스비용", "재보험비용")
    def g(d, k):
        if k not in d:
            MISSING.add(k)
            return 0.0
        return d[k][i]
    it = {}
    it["4"] = g(rA, "보험계약마진상각")
    it["5"] = g(rA, "위험조정변동")
    it["6"] = (g(rA, "예상보험금") - g(cA, "발생보험금")) + (g(rA, "예상손해조사비") - g(cA, "발생손해조사비")) + \
              (g(rA, "예상계약유지비") - g(cA, "발생계약유지비")) + (g(rA, "예상투자관리비") - g(cA, "발생투자관리비"))
    it["3sub"] = g(rA, "소계") - g(cA, "소계")
    it["8sub"] = g(rB, "소계") - g(cB, "소계")
    it["9"] = -g(cB, "보험계약마진상각")
    it["10"] = -g(cB, "위험조정변동")
    it["11"] = (g(rB, "발생재보험금") + g(rB, "발생손해조사비")) - (g(cB, "예상재보험금") + g(cB, "예상손해조사비"))
    it["7other"] = (g(rA, "기타보험수익") - g(cA, "손실부담계약관련비용") - g(cA, "발생사고요소조정") - g(cA, "기타보험서비스비용")
                    + g(rA, "보험취득현금흐름상각") - g(cA, "보험취득현금흐름상각") + g(rA, "손실요소배분액") - g(cA, "손실요소배분액"))
    it["12other"] = (g(rB, "손실회수요소관련수익") + g(rB, "발생사고요소조정") + g(rB, "손실회수요소배분액") + g(rB, "기타재보험수익")
                     - g(cB, "손실회수요소배분액") - g(cB, "기타재보험비용"))
    # subtotal self-checks
    chk = []
    for nm, d in (("rev", rA), ("rrev", rB), ("cost", cA), ("rcost", cB)):
        s = sum(v[i] for k, v in d.items() if k != "소계")
        chk.append((nm, s, d["소계"][i]))
    it["subchk"] = chk
    return it


out = []
fails = 0
MISSING = set()


def P(s):
    out.append(s)


for q, fp in FILINGS.items():
    tabs, _ = load_tables(ROOT + "/" + fp)
    revs = sect_table(tabs, "rev")
    costs = sect_table(tabs, "cost")
    P(f"##### {q} {fp} rev tables {[s for s,_ in revs]} cost tables {[s for s,_ in costs]}")
    ncol = len(revs[0][1][2]) - 1 if False else None
    # number of numeric columns
    sample = [r for r in revs[0][1] if r and r[0].replace(" ", "") == "소계"][0]
    n = len(sample) - 1
    # q3/q2: 4 cols (3M cur, cum cur, 3M prior, cum prior); q4/q1: 2 cols (cur, prior)
    if n == 4:
        cum_i, m3_i, pcum_i, pm3_i = 1, 0, 3, 2
    else:
        cum_i, m3_i, pcum_i, pm3_i = 0, None, 1, None
    c = compute(revs[0][1], costs[0][1], cum_i)
    # consistency among duplicate tables
    for (s2, r2), (s3, r3) in zip(revs[1:], costs[1:]):
        c2 = compute(r2, r3, cum_i)
        P(f"   dup table pair L{s2},L{s3} same as first: {all(c2[k]==c[k] for k in c if k!='subchk')}")
    P("   missing labels so far (treated 0): " + str(sorted(MISSING)))
    P("   sub-checks (cum): " + "; ".join(f"{nm} rows={s} printed={p}" + ("" if s == p else " MISMATCH") for nm, s, p in c["subchk"]))
    # master comparison cum
    mv = lambda it: M.get((q, it), (None, None))
    for it in ("4", "5", "6", "9", "10", "11"):
        got = mv(it)[0]
        ok = got is not None and abs(got - c[it]) < 0.5
        P(f"   item{it:>2} cum: printed {c[it]:>12.0f}  master {got}  {'OK' if ok else 'FAIL'}")
        fails += (not ok)
    m3, m8 = mv("3")[0], mv("8")[0]
    P(f"   item3 master {m3:.3f} vs printed subtotals {c['3sub']:.0f} (diff {m3-c['3sub']:+.3f}); item8 master {m8:.3f} vs {c['8sub']:.0f} (diff {m8-c['8sub']:+.3f})")
    # identities
    i7, i12 = mv("7")[0], mv("12")[0]
    v = {k: mv(k)[0] for k in ("3", "4", "5", "6", "7", "8", "9", "10", "11", "12")}
    d37 = v["3"] - v["4"] - v["5"] - v["6"] - v["7"]
    d812 = v["8"] - v["9"] - v["10"] - v["11"] - v["12"]
    P(f"   identity 3=4+5+6+7 resid {d37:+.6f}; 8=9+10+11+12 resid {d812:+.6f}")
    ok7 = abs(i7 - c["7other"]) <= 1.0
    ok12 = abs(i12 - c["12other"]) <= 1.0
    P(f"   item7 master {i7:.3f} vs other-rows {c['7other']:.0f} diff {i7-c['7other']:+.3f} {'OK' if ok7 else 'FAIL'}; item12 master {i12:.3f} vs other-rows {c['12other']:.0f} diff {i12-c['12other']:+.3f} {'OK' if ok12 else 'FAIL'}")
    fails += (abs(d37) > 1e-3) + (abs(d812) > 1e-3) + (not ok7) + (not ok12)
    # printed 3M vs master single
    if m3_i is not None:
        c3 = compute(revs[0][1], costs[0][1], m3_i)
        for it in ("4", "5", "6", "9", "10", "11", "7other", "12other"):
            key = it.replace("other", "")
            sg = mv(key)[1]
            diff = None if sg is None else sg - c3[it]
            ok = sg is not None and abs(diff) <= 1.5
            P(f"   item{key:>2} single: printed3M {c3[it]:>12.1f}  master_single {sg}  diff {diff if diff is None else round(diff,2)}  {'OK' if ok else ('NULL' if sg is None else 'FAIL')}")
            if sg is not None and not ok:
                fails += 1
    # prior-year column check -> neighbor: prior-year quarter master
    pq = {"2026.1Q": "2025.1Q", "2026.2Q": "2025.2Q"}.get(q)
    if pq:
        cp = compute(revs[0][1], costs[0][1], pcum_i)
        P(f"   NEIGHBOR prior-year col vs master {pq}:")
        for it in ("4", "5", "6", "9", "10", "11"):
            got = M.get((pq, it), (None, None))[0]
            ok = got is not None and abs(got - cp[it]) < 0.5
            P(f"      item{it:>2} prior cum printed {cp[it]:>10.0f} master {got} {'OK' if ok else 'DIFF'}")
        # derived 7/12 on prior col
        for it, key in (("7other", "7"), ("12other", "12")):
            got = M.get((pq, key), (None, None))[0]
            P(f"      item{key:>2} prior other-rows {cp[it]:.0f} master {got} diff {None if got is None else round(got-cp[it],2)}")
    P("")
P(f"TOTAL FAIL count: {fails}")
open(ROOT + "/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val/b01_abl.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
