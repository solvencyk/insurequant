# -*- coding: utf-8 -*-
"""READ-ONLY pass3 n02 (KR0032 NH농협손해보험, ticket 20261024T0600Z item 3).  Reads the separate-basis income statement + comprehensive income statement (원) of FY2024_Q1 and FY2024_Q2 and takes the PRIOR-period
CUMULATIVE column (4th numeric cell; the 3rd is the prior 3-month column) = the latest comparative of 2023.1Q / 2023.2Q.  Builds, in 백만원 (원 / 1e6, no rounding):
  20 = III.영업이익   21 = IV.영업외수익 - V.영업외비용   22 = VI.법인세차감전순이익   23 = VII.법인세비용   24 = VIII.(당기|반기)순이익   (OCI 25-32 of both quarters come from pass2/oci_read.build)
Checks: 22 - 23 = 24, 20 + 21 = 22, 31 = 24 + 25 (원-exact), the single quarter (2Q - 1Q) vs the printed prior 3-month column of the FY2024_Q2 statement.
Output: n02_is_read.json, n02_is_read.txt."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402
import oci_read as O  # noqa: E402  (pass2 reader: build(code, q, fy) for the OCI vector; main block is guarded)

sys.stdout.reconfigure(encoding="utf-8")
M, T = P.M, P.T
EVD = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/kr0032_nhfire"
CODE = "KR0032"
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{P.ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == CODE}
res, out_txt = {}, []


def PR(s=""):
    print(s)
    out_txt.append(s)


def cell(r, col):
    c = P.nums(r)[col]
    return dict(v=c[0], line=c[1], text=c[2])


for q, fy in (("2023.1Q", "FY2024_Q1"), ("2023.2Q", "FY2024_Q2"), ("2023.3Q", "FY2024_Q3")):
    d = O.read(CODE, q, fy)
    rows, labs = d["rows"], d["labs"]
    n_cols = d["n_cols"]
    assert n_cols == 4, n_cols
    PC, P3 = 3, 2

    def find(pat, exclude=None):
        hits = [r for r, L in zip(rows, labs) if re.fullmatch(pat, L) and (exclude is None or not re.search(exclude, L))]
        assert len(hits) == 1, (pat, [P.lab(h) for h in hits])
        return hits[0]

    r20 = find(r"III\.영업이익")
    r21a, r21b = find(r"IV\.영업외수익"), find(r"V\.영업외비용")
    r22 = find(r"VI\.법인세차감전순이익")
    r23 = find(r"VII\.법인세비용")
    r24 = find(r"VIII\.(당기|반기|분기)순이익")
    r25 = find(r"IX\.기타포괄손익")
    r31 = find(r"X\.총포괄손익")
    unit = d["unit"]
    assert unit == "원"
    rec = dict(file=M.rel(d["path"]), fy=fy, table=d["table"]["start"], unit=unit)
    for name, r in (("i20", r20), ("i21a", r21a), ("i21b", r21b), ("i22", r22), ("i23", r23), ("i24", r24), ("i25", r25), ("i31", r31)):
        rec[name] = cell(r, PC)
        rec[name + "_3m"] = cell(r, P3)
    mn = lambda x: x / 1e6  # noqa: E731
    v = {20: mn(rec["i20"]["v"]), 21: mn(rec["i21a"]["v"]) - mn(rec["i21b"]["v"]), 22: mn(rec["i22"]["v"]), 23: mn(rec["i23"]["v"]), 24: mn(rec["i24"]["v"])}
    v3 = {20: mn(rec["i20_3m"]["v"]), 21: mn(rec["i21a_3m"]["v"]) - mn(rec["i21b_3m"]["v"]), 22: mn(rec["i22_3m"]["v"]), 23: mn(rec["i23_3m"]["v"]), 24: mn(rec["i24_3m"]["v"])}
    rec["vals_mn"], rec["vals_3m_mn"] = {str(k): x for k, x in v.items()}, {str(k): x for k, x in v3.items()}
    # identities in 원 (exact)
    rec["chk_22_23_24_won"] = rec["i22"]["v"] - rec["i23"]["v"] - rec["i24"]["v"]
    rec["chk_20_21_22_won"] = rec["i20"]["v"] + rec["i21a"]["v"] - rec["i21b"]["v"] - rec["i22"]["v"]
    rec["chk_24_25_31_won"] = rec["i24"]["v"] + rec["i25"]["v"] - rec["i31"]["v"]
    rec["master"] = {str(i): live.get((q, i), {}).get("값") for i in (1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 31)}
    res[q] = rec
    PR(f"##### {q} <- {fy} {rec['file']} table@L{rec['table']} (원; prior cum = col 4, prior 3M = col 3)")
    for k, nm in (("i20", "III.영업이익"), ("i21a", "IV.영업외수익"), ("i21b", "V.영업외비용"), ("i22", "VI.법인세차감전순이익"), ("i23", "VII.법인세비용"), ("i24", "VIII.순이익"), ("i25", "IX.기타포괄손익"), ("i31", "X.총포괄손익")):
        PR(f"   {nm:16s} cum {rec[k]['text']:>20s}@L{rec[k]['line']}   3M {rec[k + '_3m']['text']:>20s}@L{rec[k + '_3m']['line']}")
    PR("   백만원: " + " ".join(f"{k}={x:,.6f}" for k, x in v.items()))
    PR(f"   identities (원): 22-23-24 = {rec['chk_22_23_24_won']:,.0f}; 20+IV-V-22 = {rec['chk_20_21_22_won']:,.0f}; 24+25-31 = {rec['chk_24_25_31_won']:,.0f}")
    PR("   master now: " + " ".join(f"{k}={x}" for k, x in rec["master"].items()))
# single quarter 2Q - 1Q vs printed prior 3M column of the FY2024_Q2 statement
r1, r2 = res["2023.1Q"], res["2023.2Q"]
seam = {}
for k in ("20", "21", "22", "23", "24"):
    d_ = r2["vals_mn"][k] - r1["vals_mn"][k]
    seam[k] = dict(derived=d_, printed_3m=r2["vals_3m_mn"][k], diff=d_ - r2["vals_3m_mn"][k])
res["seam_2Q_minus_1Q"] = seam
PR("single quarter 2023.2Q (cum2Q - cum1Q, 백만원) vs the printed prior 3-month column of FY2024_Q2: " + "; ".join(f"{k}: {x['derived']:,.6f} vs {x['printed_3m']:,.6f} (diff {x['diff']:+.6f})" for k, x in seam.items()))
# single quarter 2023.3Q (live 3Q cumulative - new 2Q cumulative) vs the printed prior 3M column of FY2024_Q3, and the vintage proof (FY2024_Q3 prior cumulative == live master 2023.3Q)
r3 = res["2023.3Q"]
seam3 = {}
for k in ("22", "23", "24"):
    live3 = live[("2023.3Q", int(k))]["값"]
    d_ = live3 - r2["vals_mn"][k]
    seam3[k] = dict(derived=d_, printed_3m=r3["vals_3m_mn"][k], diff=d_ - r3["vals_3m_mn"][k], prior_cum=r3["vals_mn"][k], live_master_3Q=live3, prior_cum_minus_master=r3["vals_mn"][k] - live3)
res["seam_3Q_minus_2Q"] = seam3
PR("single quarter 2023.3Q (live cum3Q - new cum2Q, 백만원) vs printed prior 3M of FY2024_Q3: " + "; ".join(f"{k}: {x['derived']:,.6f} vs {x['printed_3m']:,.6f} (diff {x['diff']:+.6f}; FY2024_Q3 prior cum - live master {x['prior_cum_minus_master']:+.6f})" for k, x in seam3.items()))
# OCI vectors (pass2 reader)
oci = {}
for q, fy in (("2023.1Q", "FY2024_Q1"), ("2023.2Q", "FY2024_Q2"), ("2023.3Q", "FY2024_Q3")):
    o, detail = O.build(CODE, q, fy)
    oci[q] = o
    PR(f"OCI {q}: " + " ".join(f"{k}={x:,.6f}" for k, x in sorted(o["vals_mn"].items())) + f" | residual 25-sum {o['residual_check']:.6f}; 31-(24+25) {o['ni_oci_total_check_won']:,.0f} 원")
res["oci"] = {q: dict(vals_mn={str(k): x for k, x in o["vals_mn"].items()}, vals_3m_mn={str(k): x for k, x in o.get("vals_3m_mn", {}).items()}, leafs=o["leafs"], i24=o["i24"], i25=o["i25"], i31=o["i31"],
                      file=o["file"], residual_check=o["residual_check"], ni_oci_total_check_won=o["ni_oci_total_check_won"]) for q, o in oci.items()}
json.dump(res, open(f"{EVD}/n02_is_read.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(f"{EVD}/n02_is_read.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out_txt) + "\n")
