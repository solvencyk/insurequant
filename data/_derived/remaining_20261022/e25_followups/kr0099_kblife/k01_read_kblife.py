# -*- coding: utf-8 -*-
"""READ-ONLY (ticket 20261023T1130Z, KR0099 KB라이프생명 2023.1Q reinsurance sub-items 9 / 10 / 11 / 12): read the PRIOR-period reinsurance rows of the separate-basis note
'(2) 당분기 및 전분기 중 기타사업비용을 제외한 보험영업수익 및 보험영업비용' of the FY2024 Q1 / H1 / Q3 reports (합계 column) with the production definitions (extract_tier2_kblife):
  9  = -|제공받은 서비스의 재보험계약마진|                         10 = -|위험해제로 인한 위험조정의 변동| (재보험비용)
  11 = |발생 재보험금 및 재보험서비스비용 회수액| - |회수예상 보험금 및 보험서비스비용|      12 = 8 - (9 + 10 + 11)  (assemble(), item 8 = live master)
H1 / Q3 tables carry [3개월 x 6 LOB | 누적 x 6 LOB] -> 합계 3개월 = numeric #6, 합계 누적 = numeric #12; the Q1 table carries 6 LOB columns -> 합계 = numeric #6.
Output k01_read_kblife.json / .txt (values + physical xml lines)."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl")
import e23_read as E  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
M, T = E.M, E.T
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/kr0099_kblife"
FY = {"2023.1Q": "FY2024_Q1", "2023.2Q": "FY2024_Q2", "2023.3Q": "FY2024_Q3"}
ROWS = {
    "re_csm": "제공받은서비스의재보험계약마진",
    "re_ra": "위험해제로인한위험조정의변동",
    "re_exp": "회수예상보험금및보험서비스비용",
    "re_act": "발생재보험금및재보험서비스비용회수액",
}
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0099"}


def nums(row):
    out = []
    for c in row["cells"][1:]:
        if c["val"] is not None:
            out.append((c["val"], c["line"], c["text"]))
        elif c["text"].strip() in ("-", "\u2212"):
            out.append((0.0, c["line"], c["text"]))
    return out


res, out_lines = {}, []


def P(s=""):
    print(s)
    out_lines.append(s)


for q, fy in FY.items():
    path = T.main_path("KR0099", fy)
    lines, s0, tabs = E.tables_sep(path)
    hits = []
    for t, rows in tabs:
        cap = E.nl(t["caption"] or "")
        if "기타사업비용을제외한" not in cap or "보험영업수익" not in cap:
            continue
        hdr = E.nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        if not re.search(r"구분(전분기|전반기|전기)", hdr):
            continue
        labs = [E.lab(r) for r in rows]
        if ROWS["re_csm"] in labs:
            hits.append((t, rows))
    if len(hits) != 1:
        raise RuntimeError(f"{path.name}: {len(hits)} prior-period note tables (need 1): {[h[0]['start'] for h in hits]}")
    t, rows = hits[0]
    unit = T.find_unit(lines, t, span=2500)
    assert unit == "백만원"
    n_total = None
    got = {}
    for key, lab in ROWS.items():
        rr = [r for r in rows if E.lab(r) == lab]
        if len(rr) != 1:
            raise RuntimeError(f"{path.name}: row {lab!r} found {len(rr)} times")
        n = nums(rr[0])
        n_total = len(n) if n_total is None else n_total
        assert len(n) == n_total, (key, len(n), n_total)
        got[key] = n
    # column layout check from the header row that lists the LOB names
    lob_hdr = next(r for r in rows if E.lab(r) == "사망")
    heads = [c["text"] for c in lob_hdr["cells"]]
    if n_total == 12:
        i_3m, i_cum = 5, 11
        assert E.nl(heads[5]) == "합계" and E.nl(heads[11]) == "합계", heads
    else:
        assert n_total == 6
        i_3m, i_cum = None, 5
        assert E.nl(heads[5]) == "합계", heads
    cum = {k: got[k][i_cum] for k in got}
    v9 = -abs(cum["re_csm"][0])
    v10 = -abs(cum["re_ra"][0])
    v11 = abs(cum["re_act"][0]) - abs(cum["re_exp"][0])
    item8 = live[(q, 8)]["값"]
    v12 = item8 - (v9 + v10 + v11)
    rec = dict(file=M.rel(path), table=t["start"], unit=unit, n_numeric=n_total, cum=dict(item9=v9, item10=v10, item11=v11, item12=v12, item8_live=item8),
               cites={k: dict(label=ROWS[k], cell_line=cum[k][1], printed=cum[k][2], value=cum[k][0]) for k in cum})
    P(f"##### {q} <- {FY[q]} {rec['file']} table@L{t['start']} unit {unit} numeric cells/row {n_total}")
    for k in ("re_csm", "re_ra", "re_act", "re_exp"):
        P(f"    {k:7s} {ROWS[k]}: cum 합계 {cum[k][0]:>8.0f} (printed {cum[k][2]!r} @L{cum[k][1]})" + (f" | 3m 합계 {got[k][i_3m][0]:.0f} (@L{got[k][i_3m][1]})" if i_3m is not None else ""))
    P(f"    -> item 9 {v9:.0f} (live {live[(q, 9)]['값']}) | item 10 {v10:.0f} (live {live[(q, 10)]['값']}) | item 11 {v11:.0f} (live {live[(q, 11)]['값']}) | item 12 = 8 - (9+10+11) = {item8:.0f} - ({v9 + v10 + v11:.0f}) = {v12:.0f} (live {live[(q, 12)]['값']})")
    if i_3m is not None:
        m9 = -abs(got["re_csm"][i_3m][0])
        m10 = -abs(got["re_ra"][i_3m][0])
        m11 = abs(got["re_act"][i_3m][0]) - abs(got["re_exp"][i_3m][0])
        rec["printed_3m"] = dict(item9=m9, item10=m10, item11=m11, lines={k: got[k][i_3m][1] for k in got})
        P(f"    printed prior 3-month: item 9 {m9:.0f} | item 10 {m10:.0f} | item 11 {m11:.0f}")
    res[q] = rec

# seam: derived single quarter (cum_q - cum_q-1, adopted vector) vs printed prior 3-month
P("\n##### seam: derived single quarter from the restated comparatives vs printed prior 3-month column")
for q, pq in (("2023.2Q", "2023.1Q"), ("2023.3Q", "2023.2Q")):
    for it in ("item9", "item10", "item11"):
        d = res[q]["cum"][it] - res[pq]["cum"][it]
        p3 = res[q]["printed_3m"][it]
        P(f"  {q} {it}: derived {d:>7.0f} (= {res[q]['cum'][it]:.0f} - {res[pq]['cum'][it]:.0f}) vs printed {p3:>7.0f} diff {d - p3:+.0f}")
json.dump(res, open(f"{EV}/k01_read_kblife.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(f"{EV}/k01_read_kblife.txt", "w", encoding="utf-8").write("\n".join(out_lines) + "\n")
