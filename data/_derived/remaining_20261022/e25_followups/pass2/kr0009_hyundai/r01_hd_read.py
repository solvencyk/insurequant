# -*- coding: utf-8 -*-
"""READ-ONLY pass2 r01 (KR0009 현대해상, ticket 20261024T0300Z item 3).  Reads the separate-basis LOB note tables (천원; columns 장기/자동차/일반/합계) of the filing that prints each quarter as the PRIOR-period
CUMULATIVE table (caption (2) 전분기 / (3) 전반기 누적 / (3) 전분기 누적 / (2) 전기) and derives, from the 장기 column (production definition):
  5 = |위험조정변동 (보험수익)|   9 = -|보험계약마진상각 (재보험서비스비용)|   10 = -|위험조정변동 (재보험서비스비용)|   (4 = |보험계약마진상각| is shown for the pairing check with the gold item 4)
Checks: the 장기 column adds up to the printed 합계 of each section (note-row sum closure); the 3-month table of the same filing (Q2/Q3: '(2) 전반기 3개월'?) is shown when present.
Output: r01_hd_read.json / .txt."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T, M = P.T, P.M
EVD = f"{P.EVP}/kr0009_hyundai"
CODE = "KR0009"
QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]
PRIOR_CAP = {"1": r"^\(2\)전분기$", "2": r"^\(3\)전반기누적$", "3": r"^\(3\)전분기누적$", "4": r"^\(2\)전기$"}
THREE_M_CAP = {"2": r"^\(4\)전반기3개월$", "3": r"^\(4\)전분기3개월$"}
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{P.ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == CODE}
out_txt, res = [], {}


def PR(s=""):
    print(s)
    out_txt.append(s)


def walk(rows):
    """sections: 보험수익 / 재보험서비스비용 -> {label: [(val,line,text) x4]}; '합계' of each section kept"""
    sec, d = None, {}
    for r in rows:
        if not r["cells"]:
            continue
        L = P.lab(r)
        n = P.nums(r)
        if L in ("보험수익", "재보험서비스비용") and not n:
            sec = L
            d.setdefault(sec, {})
            continue
        if L in ("보험수익", "재보험서비스비용") and n and all(c[2] == "" for c in n):
            sec = L
            d.setdefault(sec, {})
            continue
        if sec is None:
            continue
        if L == "합계":
            d[sec].setdefault("합계", n)
        elif L not in d[sec]:
            d[sec][L] = n
    return d


cache = {}
for q in QS:
    fy = M.later_fy(q)
    if fy not in cache:
        cache[fy] = P.load(CODE, fy)
    path, lines, s0, tabs = cache[fy]
    hits = []
    for t, rows in tabs:
        cap = P.nl(t["caption"] or "")
        if not re.match(PRIOR_CAP[q[5]], cap):
            continue
        hdr = P.nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        if not hdr.startswith("구분장기자동차일반합계"):
            continue
        labs = [P.lab(r) for r in rows]
        if "보험계약마진상각" in labs and "위험조정변동" in labs:
            hits.append((t, rows))
    if len(hits) != 1:
        raise RuntimeError(f"{q} {fy}: {len(hits)} prior LOB tables {[h[0]['start'] for h in hits]}")
    t, rows = hits[0]
    unit = T.find_unit(lines, t, span=2500)
    assert unit == "천원", unit
    d = walk(rows)
    rv, rc = d["보험수익"], d["재보험서비스비용"]
    JANG = 0

    def cell(dd, label):
        n = dd[label]
        return dict(v=n[JANG][0], line=n[JANG][1], text=n[JANG][2])

    rec = dict(file=M.rel(path), fy=fy, table=t["start"], unit=unit, caption=t["caption"])
    rec["rev_rows"] = {k: [dict(v=c[0], line=c[1], text=c[2]) for c in n] for k, n in rv.items()}
    rec["re_rows"] = {k: [dict(v=c[0], line=c[1], text=c[2]) for c in n] for k, n in rc.items()}
    it = {4: cell(rv, "보험계약마진상각"), 5: cell(rv, "위험조정변동"), 9: cell(rc, "보험계약마진상각"), 10: cell(rc, "위험조정변동")}
    rec["items_raw"] = it
    mn = lambda c: c["v"] / 1000.0  # noqa: E731
    vals = {4: abs(mn(it[4])), 5: abs(mn(it[5])), 9: -abs(mn(it[9])), 10: -abs(mn(it[10]))}
    rec["items_mn"] = vals
    # closure: 장기 column rows add up to 합계 (장기)
    s_rev = sum(n[JANG][0] for k, n in rv.items() if k != "합계")
    s_re = sum(n[JANG][0] for k, n in rc.items() if k != "합계")
    rec["closure"] = dict(rev=(s_rev, rv["합계"][JANG][0]), re=(s_re, rc["합계"][JANG][0]))
    m = {i: live.get((q, i), {}).get("값") for i in (4, 5, 9, 10)}
    rec["master"] = m
    res[q] = rec
    PR(f"##### {q} <- {fy} {rec['file']} table@L{t['start']} caption={t['caption']!r} unit {unit}")
    PR(f"  장기 column (천원): 4={it[4]['v']:,.0f}@L{it[4]['line']} 5={it[5]['v']:,.0f}@L{it[5]['line']} 9={it[9]['v']:,.0f}@L{it[9]['line']} 10={it[10]['v']:,.0f}@L{it[10]['line']}")
    PR(f"  items (백만원): 4={vals[4]:.3f} 5={vals[5]:.3f} 9={vals[9]:.3f} 10={vals[10]:.3f}   | master: 4={m[4]} 5={m[5]} 9={m[9]} 10={m[10]}")
    PR(f"  closure 장기 rows vs 합계: 보험수익 {s_rev:,.0f} vs {rv['합계'][JANG][0]:,.0f} {'OK' if abs(s_rev - rv['합계'][JANG][0]) <= 2 else 'DIFF'}; 재보험 {s_re:,.0f} vs {rc['합계'][JANG][0]:,.0f} {'OK' if abs(s_re - rc['합계'][JANG][0]) <= 2 else 'DIFF'}")
    # 3-month table (Q2/Q3 filings): print the 장기 RA/CSM of the sibling 3-month prior table, for the single-quarter check
    if q[5] in THREE_M_CAP:
        for t3, rows3 in tabs:
            cap3 = P.nl(t3["caption"] or "")
            if not re.match(THREE_M_CAP[q[5]], cap3):
                continue
            h3 = P.nl(" ".join(c["text"] for r in rows3[:3] for c in r["cells"]))
            if not h3.startswith("구분장기자동차일반합계"):
                continue
            labs3 = [P.lab(r) for r in rows3]
            if "보험계약마진상각" in labs3 and "위험조정변동" in labs3 and t3["start"] != t["start"]:
                d3 = walk(rows3)
                c5 = d3["보험수익"]["위험조정변동"][0]
                c9 = d3["재보험서비스비용"]["보험계약마진상각"][0]
                c10 = d3["재보험서비스비용"]["위험조정변동"][0]
                rec.setdefault("three_month", []).append(dict(table=t3["start"], caption=t3["caption"], c5=dict(v=c5[0], line=c5[1], text=c5[2]), c9=dict(v=c9[0], line=c9[1], text=c9[2]), c10=dict(v=c10[0], line=c10[1], text=c10[2])))
                PR(f"  3M-candidate table@L{t3['start']} caption={t3['caption']!r}: 5={c5[0]:,.0f}@L{c5[1]} 9={c9[0]:,.0f}@L{c9[1]} 10={c10[0]:,.0f}@L{c10[1]}")
json.dump(res, open(f"{EVD}/r01_hd_read.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(f"{EVD}/r01_hd_read.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out_txt) + "\n")
