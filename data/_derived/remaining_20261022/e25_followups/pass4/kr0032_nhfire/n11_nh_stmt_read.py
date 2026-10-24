# -*- coding: utf-8 -*-
"""READ-ONLY pass4 n11 (KR0032 NH농협손해보험, ticket 20261024T1000Z item 1).  Separate-basis income statement ('4. 재무제표', 원) of FY2024_Q1 / FY2024_Q2 / FY2024_Q3.  Every value is the PRIOR-period column
(statement columns = [당기 3개월, 당기 누적, 전기 3개월, 전기 누적] -> prior 3M = 3rd numeric cell, prior CUMULATIVE = 4th) = the latest comparative of 2023.1Q / 2023.2Q / 2023.3Q.
Builds in 백만원 (원 / 1e6, no rounding), production definitions verified against the live 2023.1Q gold / 2023.3Q master:
  1 = I.보험손익   16 = 3)기타사업비용   17 = II.투자손익   19 = (1)보험금융수익 + 2)재보험금융수익) - (1)보험금융비용 + 2)재보험금융비용)   18 = 17 - 19
  20 = III.영업이익   21 = IV.영업외수익 - V.영업외비용   22 = VI   23 = VII   24 = VIII
Checks (원 exact): 1 + 17 = 20; 20 + 21 = 22; 22 - 23 = 24; 투자영업수익 - 투자영업비용 = 17; 18 by the leg formula == 17 - 19.
Single quarters: 2Q (cum2Q - cum1Q) and 3Q (cum3Q - cum2Q) against the printed prior 3-month column.
Output: n11_nh_stmt_read.json / .txt"""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402
import oci_read as O  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
M = P.M
EVD = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/kr0032_nhfire"
CODE = "KR0032"
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{P.ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == CODE}
res, out_txt = {}, []


def PR(s=""):
    print(s)
    out_txt.append(s)


def cell(r, col):
    c = P.nums(r)[col]
    return dict(v=c[0], line=c[1], text=c[2])


ROWS = [
    ("i1", r"I\.보험손익"), ("i16", r"3\)기타사업비용"), ("i17", r"II\.투자손익"),
    ("inv_rev", r"1\.투자영업수익"), ("inv_exp", r"2\.투자영업비용"),
    ("ins_fin_inc", r"1\)보험금융수익"), ("re_fin_inc", r"2\)재보험금융수익"), ("ins_fin_exp", r"1\)보험금융비용"), ("re_fin_exp", r"2\)재보험금융비용"),
    ("i20", r"III\.영업이익"), ("i21a", r"IV\.영업외수익"), ("i21b", r"V\.영업외비용"), ("i22", r"VI\.법인세차감전순이익"), ("i23", r"VII\.법인세비용"), ("i24", r"VIII\.(당기|반기|분기)순이익"),
]
for q, fy in (("2023.1Q", "FY2024_Q1"), ("2023.2Q", "FY2024_Q2"), ("2023.3Q", "FY2024_Q3")):
    d = O.read(CODE, q, fy)
    rows, labs = d["rows"], d["labs"]
    assert d["n_cols"] == 4 and d["unit"] == "원", (d["n_cols"], d["unit"])
    PC, P3 = 3, 2
    rec = dict(file=M.rel(d["path"]), fy=fy, table=d["table"]["start"], unit=d["unit"])
    for key, pat in ROWS:
        hits = [r for r, L in zip(rows, labs) if re.fullmatch(pat, L)]
        assert len(hits) == 1, (q, key, pat, [P.lab(h) for h in hits])
        rec[key] = cell(hits[0], PC)
        rec[key + "_3m"] = cell(hits[0], P3)
    mn = lambda x: x / 1e6  # noqa: E731

    def vec(suffix):
        g = lambda k: rec[k + suffix]["v"]  # noqa: E731
        fin = (g("ins_fin_inc") + g("re_fin_inc")) - (g("ins_fin_exp") + g("re_fin_exp"))
        v = {1: g("i1"), 16: g("i16"), 17: g("i17"), 19: fin, 18: g("i17") - fin, 20: g("i20"), 21: g("i21a") - g("i21b"), 22: g("i22"), 23: g("i23"), 24: g("i24")}
        leg18 = (g("inv_rev") - g("ins_fin_inc") - g("re_fin_inc")) - (g("inv_exp") - g("ins_fin_exp") - g("re_fin_exp"))
        chk = dict(c_1_17_20=g("i1") + g("i17") - g("i20"), c_20_21_22=v[20] + v[21] - v[22], c_22_23_24=v[22] - v[23] - v[24], c_inv=g("inv_rev") - g("inv_exp") - g("i17"), c_18_leg=leg18 - v[18])
        return {k: x / 1e6 for k, x in v.items()}, chk
    rec["vals_mn"], rec["chk_cum_won"] = vec("")
    rec["vals_3m_mn"], rec["chk_3m_won"] = vec("_3m")
    rec["master"] = {str(i): live.get((q, i), {}).get("값") for i in (1, 16, 17, 18, 19, 20, 21, 22, 23, 24)}
    res[q] = rec
    PR(f"##### {q} <- {fy} {rec['file']} table@L{rec['table']} (원; prior cum = col 4, prior 3M = col 3)")
    for key, _p in ROWS:
        PR(f"   {key:12s} cum {rec[key]['text']:>20s}@L{rec[key]['line']}   3M {rec[key + '_3m']['text']:>20s}@L{rec[key + '_3m']['line']}")
    PR("   백만원(cum): " + " ".join(f"{k}={x:,.6f}" for k, x in rec["vals_mn"].items()))
    PR("   master now : " + " ".join(f"{k}={x}" for k, x in rec["master"].items()))
    PR("   identities (원, cum): " + "; ".join(f"{k}={v:,.0f}" for k, v in rec["chk_cum_won"].items()))
    PR("   identities (원, 3M ): " + "; ".join(f"{k}={v:,.0f}" for k, v in rec["chk_3m_won"].items()))
    PR("   cum vs live master (diff = printed - master): " + " ".join(f"{k}:{'-' if rec['master'][str(k)] is None else format(rec['vals_mn'][k] - rec['master'][str(k)], '+.6f')}" for k in (1, 16, 17, 18, 19, 20, 21, 22, 23, 24)))
# single quarters
r1, r2, r3 = res["2023.1Q"], res["2023.2Q"], res["2023.3Q"]
ITEMS = (1, 16, 17, 18, 19, 20, 21)
seam2 = {str(k): dict(derived=r2["vals_mn"][k] - r1["vals_mn"][k], printed_3m=r2["vals_3m_mn"][k], diff=r2["vals_mn"][k] - r1["vals_mn"][k] - r2["vals_3m_mn"][k]) for k in ITEMS}
seam3 = {str(k): dict(derived=r3["vals_mn"][k] - r2["vals_mn"][k], printed_3m=r3["vals_3m_mn"][k], diff=r3["vals_mn"][k] - r2["vals_mn"][k] - r3["vals_3m_mn"][k]) for k in ITEMS}
res["seam_2Q_minus_1Q"], res["seam_3Q_minus_2Q"] = seam2, seam3
PR("single quarter 2023.2Q (prior cum2Q - prior cum1Q) vs printed prior 3M of FY2024_Q2: " + "; ".join(f"{k}: {x['derived']:,.6f} vs {x['printed_3m']:,.6f} ({x['diff']:+.6f})" for k, x in seam2.items()))
PR("single quarter 2023.3Q (prior cum3Q - prior cum2Q) vs printed prior 3M of FY2024_Q3: " + "; ".join(f"{k}: {x['derived']:,.6f} vs {x['printed_3m']:,.6f} ({x['diff']:+.6f})" for k, x in seam3.items()))
json.dump(res, open(f"{EVD}/n11_nh_stmt_read.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(f"{EVD}/n11_nh_stmt_read.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out_txt) + "\n")
