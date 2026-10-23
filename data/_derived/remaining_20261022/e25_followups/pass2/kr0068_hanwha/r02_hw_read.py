# -*- coding: utf-8 -*-
"""READ-ONLY pass2 r02 (KR0068 한화생명, ticket 20261024T0300Z item 4).  Reads the separate-basis insurance-result note ('(8) ... 보험계약과 관련한 보험손익내역', LOB columns 사망/건강/연금저축/변액/기타/합계,
백만원) of the filing that prints each quarter as the PRIOR-period table ('2) 전분기/전반기/전기'), 합계 column (Q2/Q3: pair columns [3개월, 누적] x 6 -> 합계 누적 = last numeric, 합계 3개월 = second last),
and derives the PL items with the production definition (extract_tier2_life_old layout 1, companies._oll_l1_collect):
  4 = |서비스제공에 따른 보험계약마진의 변동|   5 = |위험해제에 따른 위험조정의 변동|   6 = |예상보험금 및 예상보험서비스 비용| - |실제보험금 및 실제보험서비스비용|
  9 = -|제공받은 서비스의 재보험계약마진|   10 = -|위험해제로 인한 위험조정의 변동 (재보험비용)|   11 = |발생 재보험금 및 재보험서비스비용 회수액| - |회수예상 보험금 및 보험서비스비용|
  7 = 3 - (4+5+6), 12 = 8 - (9+10+11) with the live master 3 / 8 (gold of the 2026-10-23 e21 load for 2023.1Q/2Q).
Checks: every 소 계 / 총 row = the sum of its rows (합계 누적), item 3 / 8 of the master vs note totals, derived 7 / 12 vs the sum of the OTHER rows, 3-month (합계 3개월) vs the derived single quarter."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T, M = P.T, P.M
EVD = f"{P.EVP}/kr0068_hanwha"
CODE = "KR0068"
QS = {"2023.1Q": "FY2024_Q1", "2023.2Q": "FY2024_Q2", "2023.3Q": "FY2024_Q3", "2023.4Q": "FY2024_Q4"}
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{P.ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == CODE}
out_txt, res = [], {}


def PR(s=""):
    print(s)
    out_txt.append(s)


def cellrec(c):
    return None if c is None else dict(v=c[0], line=c[1], text=c[2])


def parse(rows, pair):
    """-> list of dict(sec, label, norm, cum, m3) in document order; sec in rev/cost/re_rev/re_cost/tail"""
    out, sec = [], None
    for r in rows:
        if not r["cells"]:
            continue
        raw = P.rowtext(r)
        key = P.nl(raw)
        key2 = re.sub(r"^[0-9]+\.", "", key)
        if key.startswith("1.보험수익"):
            sec = "rev"
        elif key.startswith("2.보험서비스비용"):
            sec = "cost"
        elif key.startswith("3.재보험수익"):
            sec = "re_rev"
        elif key.startswith("4.재보험비용"):
            sec = "re_cost"
        elif key.startswith("총보험서비스결과"):
            sec = "tail"
        n = P.nums(r)
        if not n or sec is None:
            continue
        cum = cellrec(n[-1])
        m3 = cellrec(n[-2]) if pair and len(n) >= 2 else None
        out.append(dict(sec=sec, label=raw, norm=re.sub(r"^[0-9\)\(\.]+", "", key), cum=cum, m3=m3))
    return out


def find(rr, sec, needle, nth=1):
    hits = [x for x in rr if x["sec"] == sec and needle in x["norm"]]
    if len(hits) < nth:
        raise RuntimeError(f"{sec}/{needle}: {len(hits)} rows")
    return hits[nth - 1]


cache = {}
for q, fy in QS.items():
    if fy not in cache:
        cache[fy] = P.tables_with(CODE, fy, ["위험해제에따른위험조정의변동", "서비스제공에따른보험계약마진의변동"])
    path, lines, s0, tabs = cache[fy]
    prior = [(t, rows) for t, rows in tabs if re.match(r"^2\)(전분기|전반기|전기)$", P.nl(t["caption"] or ""))]
    if len(prior) != 1:
        raise RuntimeError(f"{q}: {len(prior)} prior tables {[p[0]['start'] for p in prior]}")
    t, rows = prior[0]
    unit = T.find_unit(lines, t, span=2500)
    assert unit == "백만원", unit
    hdr = P.nl(" ".join(c["text"] for r in rows[:4] for c in r["cells"]))
    pair = "3개월누적" in hdr
    rr = parse(rows, pair)
    rec = dict(file=M.rel(path), fy=fy, table=t["start"], caption=t["caption"], unit=unit, pair=pair)
    csm = find(rr, "rev", "서비스제공에따른보험계약마진의변동")
    ra = find(rr, "rev", "위험해제에따른위험조정의변동")
    exp = find(rr, "rev", "예상보험금및예상보험서비스비용")
    cact = find(rr, "cost", "실제보험금및실제보험서비스비용")
    has_re = any(x["sec"] == "re_rev" for x in rr)
    if has_re:
        ract = find(rr, "re_rev", "발생재보험금및재보험서비스비용회수액")
        rexp = find(rr, "re_cost", "회수예상보험금및보험서비스비용")
        rera = find(rr, "re_cost", "위험해제로인한위험조정의변동")
        recsm = find(rr, "re_cost", "제공받은서비스의재보험계약마진")
    rows_ = dict(csm=csm, ra=ra, exp=exp, cact=cact)
    if has_re:
        rows_.update(ract=ract, rexp=rexp, rera=rera, recsm=recsm)
    rec["rows"] = rows_
    A = lambda x: abs(x["cum"]["v"])  # noqa: E731
    it = {4: A(csm), 5: A(ra), 6: A(exp) - A(cact)}
    if has_re:
        it.update({9: -A(recsm), 10: -A(rera), 11: A(ract) - A(rexp)})
    rec["items"] = it
    if pair:
        A3 = lambda x: abs(x["m3"]["v"])  # noqa: E731
        rec["items_3m"] = {4: A3(csm), 5: A3(ra), 6: A3(exp) - A3(cact)}
        if has_re:
            rec["items_3m"].update({9: -A3(recsm), 10: -A3(rera), 11: A3(ract) - A3(rexp)})
    # subtotal / total closure: sum of rows between headers vs the 소 계 / 총 rows
    sums = {}
    for sec in ("rev", "cost", "re_rev", "re_cost"):
        rs = [x for x in rr if x["sec"] == sec]
        if not rs:
            continue
        lead = [x for x in rs if not x["norm"].startswith(("소계", "총", "보험료배분접근법적용계약"))]
        tot_sub = [x for x in rs if x["norm"] == "소계"]
        tot_paa = [x for x in rs if x["norm"].startswith("보험료배분접근법적용계약")]
        tot_all = [x for x in rs if x["norm"].startswith("총")]
        s_lead = sum(x["cum"]["v"] for x in lead)
        sums[sec] = dict(lead_sum=s_lead, subtotal=tot_sub[0]["cum"]["v"], paa=(tot_paa[0]["cum"]["v"] if tot_paa else 0.0), total=tot_all[0]["cum"]["v"], n_lead=len(lead))
    rec["sums"] = sums
    i3_note = sums["rev"]["total"] - sums["cost"]["total"]
    i8_note = (sums["re_rev"]["total"] - sums["re_cost"]["total"]) if has_re else None
    m = {i: live.get((q, i), {}).get("값") for i in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12)}
    rec["master"] = m
    rec["i3_note"], rec["i8_note"] = i3_note, i8_note
    new4 = m[4] if m[4] is not None else it[4]
    i7 = m[3] - (new4 + it[5] + it[6])
    i12 = (m[8] - (it[9] + it[10] + it[11])) if has_re else None
    rec["items"]["7"], rec["items"]["12"] = i7, i12
    # independent "other rows" sums
    rev_other = [x for x in rr if x["sec"] == "rev" and x["norm"] not in ("소계",) and not x["norm"].startswith("총") and x is not csm and x is not ra and x is not exp]
    cost_other = [x for x in rr if x["sec"] == "cost" and x["norm"] not in ("소계",) and not x["norm"].startswith("총") and x is not cact]
    other7 = sum(x["cum"]["v"] for x in rev_other) - sum(x["cum"]["v"] for x in cost_other)
    rec["closure7"] = dict(rev_other=[x["label"] for x in rev_other], cost_other=[x["label"] for x in cost_other], value=other7, derived=i7, diff=i7 - other7)
    if pair:
        o3 = sum(x["m3"]["v"] for x in rev_other) - sum(x["m3"]["v"] for x in cost_other)
        rec["other7_3m"] = o3
    if has_re:
        rr_other = [x for x in rr if x["sec"] == "re_rev" and x["norm"] not in ("소계",) and not x["norm"].startswith("총") and x is not ract]
        rc_other = [x for x in rr if x["sec"] == "re_cost" and x["norm"] not in ("소계",) and not x["norm"].startswith("총") and x not in (rexp, rera, recsm)]
        other12 = sum(x["cum"]["v"] for x in rr_other) - sum(x["cum"]["v"] for x in rc_other)
        rec["closure12"] = dict(rr_other=[x["label"] for x in rr_other], rc_other=[x["label"] for x in rc_other], value=other12, derived=i12, diff=i12 - other12)
        if pair:
            rec["other12_3m"] = sum(x["m3"]["v"] for x in rr_other) - sum(x["m3"]["v"] for x in rc_other)
    rec["lines"] = {k: x["cum"]["line"] for k, x in rec["rows"].items()}
    res[q] = rec
    PR(f"##### {q} <- {fy} {rec['file']} table@L{t['start']} caption={t['caption']!r} pair={pair}")
    PR("  rows (합계 누적): " + "; ".join(f"{k}={x['cum']['text']}@L{x['cum']['line']}" for k, x in rec["rows"].items()))
    PR("  items:  " + " ".join(f"{k}={v:,.3f}" for k, v in it.items() if v is not None) + f"  | master: " + " ".join(f"{k}={m[k]}" for k in (4, 5, 6, 9, 10, 11)))
    PR("  section sums (rows vs 소계 / +PAA vs 총): " + "; ".join(f"{s}: {v['lead_sum']:,.0f} vs {v['subtotal']:,.0f}{' OK' if abs(v['lead_sum'] - v['subtotal']) <= 2 else ' DIFF'}, +{v['paa']:,.0f} vs 총 {v['total']:,.0f}{' OK' if abs(v['subtotal'] + v['paa'] - v['total']) <= 2 else ' DIFF'}" for s, v in sums.items()))
    PR(f"  3: master {m[3]} vs note 총수익-총비용 {i3_note:,.0f}; 8: master {m[8]} vs note {i8_note}")
    PR(f"  derived 7 = {i7:,.3f} vs other-rows {other7:,.0f} (diff {i7 - other7:+.3f})" + (f"; derived 12 = {i12:,.3f} vs other-rows {rec['closure12']['value']:,.0f} (diff {rec['closure12']['diff']:+.3f})" if has_re else "; (no 재보험 sections in this table)"))
    if pair:
        PR("  3M (합계 3개월): " + " ".join(f"{k}={v:,.0f}" for k, v in rec["items_3m"].items()) + f" | other7_3m={rec['other7_3m']:,.0f}" + (f" other12_3m={rec['other12_3m']:,.0f}" if has_re else ""))
json.dump(res, open(f"{EVD}/r02_hw_read.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(f"{EVD}/r02_hw_read.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out_txt) + "\n")
