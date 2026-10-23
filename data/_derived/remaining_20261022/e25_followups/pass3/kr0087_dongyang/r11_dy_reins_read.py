# -*- coding: utf-8 -*-
"""READ-ONLY pass3 r11 (KR0087 동양생명, ticket 20261024T0600Z item 2).  Reads the separate-basis 재보험수익 / 재보험비용 분석 공시 tables (columns [3개월, 누적]) of the FY2025_Q2 half-year report.
Document order is [당반기, 전반기]; the CURRENT-period pair is cross-checked against the live master 2025.2Q (item 9 = -878, 10 = -565, 11 = 7,026) to prove the label -> item mapping and the table order,
then the PRIOR-period pair (= 2024.2Q cumulative, the latest comparative) is turned into the production items (extract_tier2_dongyang definitions):
  9 = -|보험계약마진 (서비스의 이전으로 당기손익에 인식한 보험계약마진)|     10 = -|비금융위험에 대한 위험조정의 변동분|
  11 = |재보험수익, 발생한 보험금 (+ 발생한 손해조사비)| - |재보험비용, 예상 보험금 (기초 예상 측정치) (+ 예상 기타 보험서비스비용)|     12 = 8 - (9+10+11)  (8 = live master)
Also records the printed signs (the 재보험비용 components print the CONTRIBUTION sign: their sum is minus the printed total) and the note-level result (재보험수익 total - 재보험비용 total).
FY2025_Q3 (2024.3Q prior-period tables) is probed too: its 재보험 분석 tables carry TOTALS ONLY, so no 3Q detail can be read.
Output: r11_dy_reins_read.json / .txt."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T, M = P.T, P.M
EVD = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/kr0087_dongyang"
CODE = "KR0087"
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{P.ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == CODE}
out_txt, res = [], {}


def PR(s=""):
    print(s)
    out_txt.append(s)


def cellrec(c):
    return None if c is None else dict(v=c[0], line=c[1], text=c[2])


def rowkey(r):
    return P.nl(" ".join(c["text"] for c in r["cells"][:2] if c["val"] is None and not re.fullmatch(r"[\(\)\d,\-\s]+", c["text"] or "")))


def rows_of(tab):
    t, rows = tab
    out = []
    for r in rows:
        vals = [(c["val"] if c["val"] is not None else 0.0, c["line"], c["text"]) for c in r["cells"] if (c["val"] is not None or c["text"].strip() in ("-", "\u2212")) and re.fullmatch(r"[\(\)\d,\-\u2212\s]+", c["text"].strip() or "x")]
        if len(vals) >= 2:
            out.append(dict(key=rowkey(r), cum=cellrec(vals[-1]), m3=cellrec(vals[-2]), tr=r["tr_line"]))
    return out


def analysis(tabs, must):
    out = []
    for t, rows in tabs:
        hdr = P.nl(" ".join(cc["text"] for x in rows[:6] for cc in x["cells"]))
        if "3개월" in hdr and "누적" in hdr and must in P.nl(" ".join(cc["text"] for x in rows for cc in x["cells"][:2])):
            out.append((t, rows))
    return out


def pick(rr, needle, exclude=()):
    hits = [x for x in rr if needle in x["key"] and not any(e in x["key"] for e in exclude)]
    assert len(hits) == 1, (needle, [x["key"] for x in rr])
    return hits[0]


fy = "FY2025_Q2"
path, lines, s0, rev_tabs = P.tables_with(CODE, fy, ["재보험수익,발생한보험금"])
_p, _l, _s, cost_tabs = P.tables_with(CODE, fy, ["재보험비용,예상보험금"])
rt, ct = analysis(rev_tabs, "재보험수익,발생한보험금"), analysis(cost_tabs, "재보험비용,예상보험금")
assert len(rt) == 2 and len(ct) == 2, (len(rt), len(ct))
unit = T.find_unit(lines, rt[1][0], span=2500)
assert unit == "백만원", unit
rec = dict(file=M.rel(path), fy=fy, unit=unit, rev_tables=[x[0]["start"] for x in rt], cost_tables=[x[0]["start"] for x in ct])


def vec(rev_tab, cost_tab):
    rr, cc = rows_of(rev_tab), rows_of(cost_tab)
    d = dict(
        rev_total=[x for x in rr if x["key"] == P.nl("재보험자에게서 회수한 금액에서 생기는 수익")][0],
        act=pick(rr, "재보험수익,발생한보험금"), act_survey=pick(rr, "재보험수익,발생한손해조사비"),
        rev_future=pick(rr, "재보험수익,미래서비스"), rev_past=pick(rr, "재보험수익,과거서비스"),
        cost_total=[x for x in cc if x["key"] == P.nl("재보험자에게 지급된 보험료 배분액에서 생기는 비용")][0],
        exp=pick(cc, "재보험비용,예상보험금"), exp_other=pick(cc, "재보험비용,예상기타보험서비스비용"),
        ra=pick(cc, "재보험비용,비금융위험에대한위험조정의변동분"), csm=pick(cc, "재보험비용,서비스의이전으로당기손익에인식한보험계약마진"), other=pick(cc, "재보험비용,그밖의금액"))
    return d


def items(d, col):
    g = lambda k: d[k][col]["v"]  # noqa: E731
    i9, i10 = -abs(g("csm")), -abs(g("ra"))
    i11 = (abs(g("act")) + abs(g("act_survey"))) - (abs(g("exp")) + abs(g("exp_other")))
    return i9, i10, i11


for tag, idx in (("current", 0), ("prior", 1)):
    d = vec(rt[idx], ct[idx])
    rec[tag] = d
    i9, i10, i11 = items(d, "cum")
    j9, j10, j11 = items(d, "m3")
    rec[tag + "_items_cum"] = {"9": i9, "10": i10, "11": i11}
    rec[tag + "_items_3m"] = {"9": j9, "10": j10, "11": j11}
    # closure of the two tables: components sum to minus the printed totals
    rsum = sum(d[k]["cum"]["v"] for k in ("act", "act_survey", "rev_future", "rev_past"))
    csum = sum(d[k]["cum"]["v"] for k in ("exp", "exp_other", "ra", "csm", "other"))
    rec[tag + "_closure"] = dict(rev_components_sum=rsum, rev_total=d["rev_total"]["cum"]["v"], cost_components_sum=csum, cost_total=d["cost_total"]["cum"]["v"],
                                 note_result=d["rev_total"]["cum"]["v"] - d["cost_total"]["cum"]["v"])
    PR(f"##### {tag} pair <- {rec['file']} rev@L{rt[idx][0]['start']} cost@L{ct[idx][0]['start']}")
    for k in ("rev_total", "act", "act_survey", "rev_future", "rev_past", "cost_total", "exp", "exp_other", "ra", "csm", "other"):
        PR(f"   {k:11s} {d[k]['key'][:58]:58s} 3M {d[k]['m3']['text']:>9s}@L{d[k]['m3']['line']}  cum {d[k]['cum']['text']:>9s}@L{d[k]['cum']['line']}")
    PR(f"   items (cum): 9 = -|CSM| = {i9:,.0f}; 10 = -|RA| = {i10:,.0f}; 11 = |act| - |exp| = {i11:,.0f}   | 3M: {j9:,.0f} / {j10:,.0f} / {j11:,.0f}")
    PR(f"   closure: revenue components {rsum:,.0f} (= - printed total {d['rev_total']['cum']['v']:,.0f}); cost components {csum:,.0f} (= - printed total {d['cost_total']['cum']['v']:,.0f}); note result {rec[tag + '_closure']['note_result']:,.0f}")
# sanity: the current pair must reproduce the live master 2025.2Q
m25 = {i: live[("2025.2Q", i)]["값"] for i in (8, 9, 10, 11, 12)}
c = rec["current_items_cum"]
rec["sanity_2025_2Q"] = dict(master=m25, table=c, ok=(abs(m25[9] - c["9"]) <= 1 and abs(m25[10] - c["10"]) <= 1 and abs(m25[11] - c["11"]) <= 1))
PR(f"SANITY current pair vs live master 2025.2Q: master 9/10/11 = {m25[9]}/{m25[10]}/{m25[11]}; tables {c['9']:,.0f}/{c['10']:,.0f}/{c['11']:,.0f} -> {'OK' if rec['sanity_2025_2Q']['ok'] else 'MISMATCH'}")
assert rec["sanity_2025_2Q"]["ok"]
# 2024.2Q vector
p9, p10, p11 = items(rec["prior"], "cum")
m8 = live[("2024.2Q", 8)]["값"]
p12 = m8 - (p9 + p10 + p11)
rec["q2024_2Q"] = dict(i8=m8, i9=p9, i10=p10, i11=p11, i12=p12, master_now={str(i): live[("2024.2Q", i)]["값"] for i in (8, 9, 10, 11, 12)})
cl = rec["prior_closure"]
# residual vs the other rows under the production sign convention: other = (act_survey-free) rev_future + rev_past - exp_other - other + [csm printed credit -> production sign flip 2*|csm| when printed positive]
d = rec["prior"]
csm_printed = d["csm"]["cum"]["v"]
other_rows = (abs(d["rev_future"]["cum"]["v"]) * (1 if d["rev_future"]["cum"]["v"] < 0 else -1) + abs(d["rev_past"]["cum"]["v"]) * (1 if d["rev_past"]["cum"]["v"] < 0 else -1)) - (-d["other"]["cum"]["v"]) - (-d["exp_other"]["cum"]["v"])
rec["q2024_2Q"]["other_rows_printed_sign"] = other_rows
rec["q2024_2Q"]["i12_printed_sign_convention"] = m8 - (csm_printed + d["ra"]["cum"]["v"] + p11)
rec["q2024_2Q"]["i9_printed_sign"], rec["q2024_2Q"]["i10_printed_sign"] = csm_printed, d["ra"]["cum"]["v"]
rec["q2024_2Q"]["diff_i12_vs_other_rows_printed_sign"] = rec["q2024_2Q"]["i12_printed_sign_convention"] - other_rows
PR("2024.2Q cumulative vector (production sign convention 9 = -|CSM|, 10 = -|RA|):")
PR(f"   8 (live master) = {m8:.6f}; 9 = {p9:,.0f}; 10 = {p10:,.0f}; 11 = {p11:,.0f}; 12 = 8 - (9+10+11) = {p12:.6f}; identity 8 - (9+10+11+12) = {m8 - (p9 + p10 + p11 + p12):.6f}")
PR(f"   master now: 8={m8} 9={live[('2024.2Q', 9)]['값']} 10={live[('2024.2Q', 10)]['값']} 11={live[('2024.2Q', 11)]['값']} 12={live[('2024.2Q', 12)]['값']}")
PR(f"   printed CSM sign: {csm_printed:+,.0f} (a CREDIT in the 재보험비용 table: components print the contribution sign); with the printed sign 9 = {csm_printed:+,.0f}, 10 = {d['ra']['cum']['v']:+,.0f} and 12 = {rec['q2024_2Q']['i12_printed_sign_convention']:.6f}")
PR(f"   other rows (미래·과거 서비스 + 그 밖의 금액 + 예상 기타, contribution sign) = {other_rows:,.0f} vs 12 (printed-sign convention) {rec['q2024_2Q']['i12_printed_sign_convention']:.3f} -> diff {rec['q2024_2Q']['diff_i12_vs_other_rows_printed_sign']:+.3f}")
PR(f"   note result {cl['note_result']:,.0f} (재보험수익 {cl['rev_total']:,.0f} - 재보험비용 {cl['cost_total']:,.0f}) vs master 8 {m8:.3f}: {m8 - cl['note_result']:+.3f} (the original FY2024_Q2 prints 재보험비용 26,158: note result 4,327)")
# probe of FY2025_Q3: totals only?
fy3 = "FY2025_Q3"
path3, lines3, s03, tabs3 = P.tables_with(CODE, fy3, ["재보험"])
probe = []
for t, rows in tabs3:
    labs = [P.nl(" ".join(c["text"] for c in r["cells"][:2])) for r in rows if r["cells"]]
    hdr = P.nl(" ".join(cc["text"] for x in rows[:6] for cc in x["cells"]))
    if "3개월" in hdr and "누적" in hdr and any(x in " ".join(labs) for x in ("재보험수익", "재보험비용", "보험서비스결과")) and len(rows) <= 12:
        probe.append(dict(table=t["start"], rows=[(x, [c["text"] for c in r["cells"] if c["text"].strip()][:9]) for x, r in ((r["tr_line"], r) for r in rows) if r["cells"]]))
rec["fy2025_q3_probe"] = probe
PR(f"FY2025_Q3 probe ({M.rel(path3)}): {len(probe)} small [3개월, 누적] reinsurance tables; row labels: {sorted({P.nl(' '.join(r[1][:1])) for p in probe for r in p['rows'] if r[1]})[:14]}")
json.dump(rec, open(f"{EVD}/r11_dy_reins_read.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
open(f"{EVD}/r11_dy_reins_read.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out_txt) + "\n")
