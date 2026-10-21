# -*- coding: utf-8 -*-
"""Independent re-derivation of Kyobo (KR0073) CSM waterfall items 1-6 (separate basis, YTD, 억원) from raw DART XML.
No scripts/ or src/ imports. Source = latest filing that prints the period as a comparative column (else the filing itself)."""
import sys, json, re
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from vreader import *
from vfiles import main_xml

def S(x): return re.sub(r"\s", "", x)

def issued_tables(fy):
    T = read_tables(main_xml(fy)); out = []
    for t in T:
        if "5.재무제표주석" not in S(t["title"]): continue
        hdr = S(" ".join(c for r in t["rows"][:4] for c in r["cells"]))
        if "보험계약마진" in hdr and "미래현금흐름" in hdr and any(S(r["cells"][0]).startswith("1.기초보험계약") for r in t["rows"] if r["cells"]):
            out.append(t)
    return out

CSMCOL = 5   # 0-based index among numeric cells: PV, RA, 완전소급, 공정가치, 그 밖, 소계(=5), total

def vec(t):
    def val(pred, nth=0):
        hits = [r for r in t["rows"] if r["cells"] and pred(S(r["cells"][0]))]
        r = hits[nth]
        nums = [num(c) for c in r["cells"][1:]]
        v = nums[CSMCOL]
        return (0.0 if v is None else v), r["line"]
    d = {}
    d["open"] = val(lambda l: "기초" in l and "순부채" in l)
    d["est"] = val(lambda l: l.startswith("(1)보험계약마진을조정하는추정치"))
    d["loss"] = val(lambda l: l.startswith("(2)손실부담계약집합"))
    d["new"] = val(lambda l: l.startswith("(3)최초인식한계약의효과"))
    d["rel"] = val(lambda l: l.startswith("(1)서비스이전을반영하기위해"))
    d["fin"] = val(lambda l: l.startswith("6.보험금융손익"))
    d["oth"] = val(lambda l: l.startswith("7.기타"))
    d["close"] = val(lambda l: "말" in l and "순부채" in l)
    return d

def add(a, b): return {k: (a[k][0] + b[k][0], f"{a[k][1]}+{b[k][1]}") for k in a}

# quarter -> (filing, [table indices among issued tables]) ; prior-column table = index 1 for 1-block filings
PLAN = {
 "2023.1Q": ("FY2024_Q1", [1]), "2023.2Q": ("FY2024_Q2", [1]), "2023.3Q": ("FY2024_Q3", [1]), "2023.4Q": ("FY2024_Q4", [1]),
 "2024.1Q": ("FY2025_Q1", [1]), "2024.2Q": ("FY2025_Q2", [1]), "2024.3Q": ("FY2025_Q3", [1]), "2024.4Q": ("FY2025_Q4", [3, 4, 5]),
 "2026.1Q": ("FY2026_Q1", [0, 1, 2]),
}
cs = json.load(open("CSM_waterfall.json", encoding="utf-8"))
M = {(r["공시분기"], int(r["항목번호"])): (r["값"], r["값_당분기"]) for r in cs if r["원수사명"] == "교보생명보험"}
bad = 0; ncell = 0
# 2024.3Q/4Q masters were not touched by this commit and carry 1 decimal (0.1억); 2026.1Q item1/item4 carry the same 1-dec rounding of item1
TOL = {"2024.3Q": 0.1, "2024.4Q": 0.1, "2026.1Q": 0.0151}
for q, (fy, idxs) in PLAN.items():
    try:
        tabs = issued_tables(fy)
    except Exception as e:
        print(q, fy, "ERR", type(e).__name__, e); continue
    print(f"== {q} {fy} issued-contract CSM tables found={[t['line'] for t in tabs]} using={[tabs[i]['line'] for i in idxs]}")
    v = None
    for i in idxs:
        x = vec(tabs[i]); v = x if v is None else add(v, x)
    o, e, l, n, r, f, ot, c = (v[k][0] for k in ("open", "est", "loss", "new", "rel", "fin", "oth", "close"))
    resid = c - o - n - f - r
    printed_adj = e + l + ot
    raw = {1: o / 100, 2: n / 100, 3: f / 100, 4: resid / 100, 5: r / 100, 6: c / 100}
    print(f"   raw 백만원: open={o:,.0f} est={e:,.0f} loss={l:,.0f} new={n:,.0f} rel={r:,.0f} fin={f:,.0f} oth={ot:,.0f} close={c:,.0f} | residual={resid:,.0f} vs printed(est+loss+oth)={printed_adj:,.0f} gap={resid-printed_adj:,.0f}")
    for it in range(1, 7):
        m = M.get((q, it))
        tol = TOL.get(q, 0.0051)
        ok = m is not None and abs(raw[it] - m[0]) <= tol
        ncell += 1; bad += (not ok)
        print(f"   item{it}: raw={raw[it]:>11.2f} master={m[0] if m else None!s:>11} {'OK' if ok else 'MISMATCH'}   lines open={v['open'][1]} close={v['close'][1]}")
print(f"CSM cells compared={ncell} mismatches={bad}")
