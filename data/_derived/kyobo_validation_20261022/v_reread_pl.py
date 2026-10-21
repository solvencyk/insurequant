# -*- coding: utf-8 -*-
"""Independent re-derivation of Kyobo (KR0073) separate-basis PL items for 2023.1Q-2024.2Q (YTD) from raw DART XML.
Does not import scripts/ or src/. Source per quarter = latest filing that prints the period as a comparative column.
Compare with PL_breakdown.json (value field '값', YTD, 백만원)."""
import sys, json, re
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from vreader import *
from vfiles import main_xml

# quarter -> (filing folder for latest comparative, header token of the wanted period, which numeric column index)
PLAN = {
 "2023.1Q": ("FY2024_Q1", "제 67 기 1분기", 3),
 "2023.2Q": ("FY2024_Q2", "제 67 기 반기", 3),
 "2023.3Q": ("FY2024_Q3", "제 67 기 3분기", 3),
 "2023.4Q": ("FY2024_Q4", "제 67 기", 1),
 "2024.1Q": ("FY2025_Q1", "제 68 기 1분기", 3),
 "2024.2Q": ("FY2025_Q2", "제 68 기 반기", 3),
 "2024.3Q": ("FY2025_Q3", "제 68 기 3분기", 3),   # unchanged check (if filing present)
 "2024.4Q": ("FY2025_Q4", "제 68 기", 1),
}
ORIG = {"2023.1Q": ("FY2023_Q1", 1), "2023.2Q": ("FY2023_Q2", 1), "2023.3Q": ("FY2023_Q3", 1), "2023.4Q": ("FY2023_Q4", 0),
        "2024.1Q": ("FY2024_Q1", 1), "2024.2Q": ("FY2024_Q2", 1), "2024.3Q": ("FY2024_Q3", 1), "2024.4Q": ("FY2024_Q4", 0)}

def nz(s):
    return s.replace(" ", "")

def find_pl(T):
    c = []
    for t in T:
        if t["title"].replace(" ", "") in ("나.포괄손익계산서", "나.포괄손익계산서") and any(r["cells"] and r["cells"][0] == "보험손익" for r in t["rows"]):
            c.append(t)
    assert len(c) >= 1, "no separate PL"
    return c[0]

def base(lbl):
    return re.sub(r"\(.*?\)", "", nz(lbl))

def row(t, label, nth=0):
    labels = label if isinstance(label, (list, tuple)) else [label]
    hits = [r for r in t["rows"] if r["cells"] and base(r["cells"][0]) in [nz(x) for x in labels]]
    return hits[nth] if len(hits) > nth else None

def derive(fy, idx, label_probe=None):
    f = main_xml(fy); T = read_tables(f); t = find_pl(T)
    hdr = " ".join(c for r in t["rows"][:3] for c in r["cells"])
    def v(label, nth=0):
        r = row(t, label, nth)
        if r is None: return None, None
        nums = [num(c) for c in r["cells"][1:]]
        val = nums[idx] if idx < len(nums) else None
        return (None if val is None else val / 1e6), r["line"]
    out = {}
    out[1] = v("보험손익")
    out[17] = v("투자손익")
    # item19 = 재보험금융수익 - 보험금융비용 - 재보험금융비용 (+ 보험금융수익 if printed)
    ri, l1 = v("재보험금융수익"); fe, l2 = v("보험금융비용"); re_, l3 = v("재보험금융비용"); fi, l4 = v("보험금융수익")
    out[19] = ((ri or 0) - (fe or 0) - (re_ or 0) + (fi or 0), f"{l1},{l2},{l3},{l4}")
    out[20] = v("영업이익")
    out[22] = v(["법인세차감전순이익", "법인세비용차감전순이익"])
    out[23] = v(["법인세비용", "법인세수익(비용)", "법인세비용(수익)"])
    out[24] = v(["당기순이익", "분기순이익", "반기순이익"])
    out[25] = v("기타포괄손익", 0)
    out[31] = v(["총포괄손익", "분기총포괄손익", "반기총포괄손익", "당기총포괄손익", "연결반기총포괄손익"])
    return f, t["line"], hdr, out

def main():
    pl = json.load(open("PL_breakdown.json", encoding="utf-8"))
    master = {}
    for r in pl:
        if r["원수사명"] == "교보생명보험":
            master[(r["공시분기"], int(r["항목번호"]))] = r["값"]
    mism = []; n = 0
    for q, (fy, tok, idx) in PLAN.items():
        try:
            f, tline, hdr, out = derive(fy, idx)
        except Exception as e:
            print(q, fy, "SKIP", type(e).__name__, e); continue
        print(f"== {q}  latest-comparative filing {f}  table@{tline}  header={hdr[:90]}")
        assert tok.replace(" ", "") in hdr.replace(" ", ""), (q, tok, hdr)
        for it, (val, ln) in out.items():
            m = master.get((q, it))
            ok = val is not None and m is not None and abs(val - m) <= 0.01
            n += 1
            if not ok: mism.append((q, it, val, m, ln))
            print(f"   item{it:>2} raw={val!s:>22} master={m!s:>22} line={ln} {'OK' if ok else 'MISMATCH'}")
        # original (same-period) filing for the record
        of, oidx = ORIG[q]
        try:
            _, _, _, oout = derive(of, oidx)
            diffs = {it: (oout[it][0], master.get((q, it))) for it in oout if oout[it][0] is not None and master.get((q, it)) is not None and abs(oout[it][0] - master[(q, it)]) > 0.01}
            print("   original-vintage differs from master at:", {k: (round(a, 3), round(b, 3)) for k, (a, b) in diffs.items()} or "none")
        except Exception as e:
            print("   original filing:", type(e).__name__, e)
    print(f"\nPL cells compared={n} mismatches={len(mism)}")
    for x in mism: print("  MISMATCH", x)
main()
