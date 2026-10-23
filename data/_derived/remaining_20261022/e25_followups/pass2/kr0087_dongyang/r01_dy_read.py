# -*- coding: utf-8 -*-
"""READ-ONLY pass2 r01 (KR0087 동양생명, ticket 20261024T0300Z item 2).  For 2024.2Q (FY2025 H1 report) and 2024.3Q (FY2025 Q3 report) read the PRIOR-period tables '보험수익 분석 공시' and '발행보험의 보험서비스비용 분석 공시'
(separate basis, 백만원, columns [3개월, 누적]) and derive, with the production/generic definitions that are already in the master for 2024.1Q (Q1: 3M = cumulative):
  5 = |위험조정 변동|(누적)   6 = 예상 발생보험금(누적) - 실제 발생보험금(누적)   (claims only: 2024.1Q master 831 = 136,816 - 135,985)   4 = |제공된 서비스의 보험계약마진|(누적) (gold already, shown for the pairing check)
  7 = 3 - (4+5+6) with the live master 3 (statement level) ; closure against the OTHER rows of the same two tables.
The master holds the 3-month column for items 5 / 6 of 2024.2Q and 2024.3Q (OTHER_MASTER_HOLDS_3M of the sweep).  Output: r01_dy_read.json / .txt."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T, M = P.T, P.M
EVD = f"{P.EVP}/kr0087_dongyang"
CODE = "KR0087"
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{P.ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == CODE}
out_txt, res = [], {}


def PR(s=""):
    print(s)
    out_txt.append(s)


def cellrec(c):
    return None if c is None else dict(v=c[0], line=c[1], text=c[2])


def rowkey(r):
    """normalised text of the first two cells (section label + row label in the classic dialect, the row label alone in the XBRL dialect)"""
    return P.nl(" ".join(c["text"] for c in r["cells"][:2] if c["val"] is None and not re.fullmatch(r"[\(\)\d,\-\s]+", c["text"] or "")))


def rows_of(tab):
    t, rows = tab
    out = []
    for r in rows:
        n = P.nums(r, skip=1)
        if not n:
            continue
        # the first numeric cell may sit in cell 1 (when cell 0 is a section label) -> take numbers from the cells that are numeric only
        vals = [(c["val"] if c["val"] is not None else 0.0, c["line"], c["text"]) for c in r["cells"] if (c["val"] is not None or c["text"].strip() in ("-", "\u2212")) and re.fullmatch(r"[\(\)\d,\-\u2212\s]+", c["text"].strip() or "x")]
        if len(vals) >= 2:
            out.append(dict(key=rowkey(r), cum=cellrec(vals[-1]), m3=cellrec(vals[-2]), tr=r["tr_line"], first_label=r["cells"][0]["text"]))
    return out


def pick(rr, needle, nth=1, exclude=()):
    hits = [x for x in rr if needle in x["key"] and not any(e in x["key"] for e in exclude)]
    if len(hits) < nth:
        raise RuntimeError(f"{needle}: {len(hits)} rows, keys={[x['key'] for x in rr]}")
    return hits[nth - 1]


# ------------------------------------------------------------------------------------------------ 2024.2Q <- FY2025_Q2 (classic tag-per-line dialect)
cfg = {
    "2024.2Q": dict(fy="FY2025_Q2",
                    rev_needles=["위험조정변동", "제공된서비스의보험계약마진", "예상발생보험금"],
                    cost_needles=["실제발생보험금", "발생사고부채변동", "손실부담계약인식및환입"],
                    ra="위험조정변동", csm="제공된서비스의보험계약마진", exp="예상발생보험금", exp2="예상기타보험서비스비용", acq="보험취득현금흐름회수", loss="손실요소배분액", total_rev="보험수익",
                    act="실제발생보험금", act2="실제기타보험서비스비용", c_loss_contract="손실부담계약인식및환입", c_ibnr="발생사고부채변동", c_acq="보험취득현금흐름상각", c_lossalloc="손실요소배분액", c_other="기타", total_cost="발생한보험계약에서생기는보험서비스비용"),
    "2024.3Q": dict(fy="FY2025_Q3",
                    rev_needles=["보험수익,비금융위험에대한위험조정의변동분"],
                    cost_needles=["보험서비스비용,발생한보험금", "보험서비스비용,기타영업비용"],
                    ra="비금융위험에대한위험조정의변동분", csm="서비스의이전으로당기손익에인식한보험계약마진", exp="예상보험금", exp2="예상기타보험서비스비용", acq="보험취득현금흐름의회수", loss="손실요소배분액", total_rev="보험수익",
                    act="보험서비스비용,발생한보험금", act2="그밖의발생한보험서비스비용", c_future="미래서비스와관련된변동분", c_past="과거서비스와관련된금액", c_acq="보험취득현금흐름의상각", c_lossalloc="손실요소배분액", c_other="기타영업비용", total_cost="발행한보험계약에서생기는보험서비스비용"),
}
for q, c in cfg.items():
    fy = c["fy"]
    path, lines, s0, rev_tabs = P.tables_with(CODE, fy, c["rev_needles"])
    _p2, _l2, _s2, cost_tabs = P.tables_with(CODE, fy, c["cost_needles"])
    # drop roll-forward tables (they carry 잔여보장 / 기초 words) and keep the analysis tables with exactly the [3개월, 누적] header
    def analysis(tabs, must):
        out = []
        for t, rows in tabs:
            blob = P.nl(" ".join(x["cells"][0]["text"] for x in rows if x["cells"]))
            hdr = P.nl(" ".join(cc["text"] for x in rows[:6] for cc in x["cells"]))
            if "3개월" in hdr and "누적" in hdr and not any(k in blob for k in ("기말", "잔여보장", "기초보험계약", "기초장부금액")) and must in P.nl(" ".join(cc["text"] for x in rows for cc in x["cells"][:2])):
                out.append((t, rows))
        return out
    rt = analysis(rev_tabs, "위험조정")
    ct = analysis(cost_tabs, "손실요소")
    if len(rt) != 2 or len(ct) != 2:
        raise RuntimeError(f"{q}: {len(rt)} revenue / {len(ct)} cost analysis tables (need 2+2): {[x[0]['start'] for x in rt]} {[x[0]['start'] for x in ct]}")
    rev_t, cost_t = rt[1], ct[1]          # document order = [당기, 전기]: the second one is the PRIOR period
    rrr, ccc = rows_of(rev_t), rows_of(cost_t)
    unit = T.find_unit(lines, rev_t[0], span=2500)
    assert unit == "백만원", unit
    rec = dict(file=M.rel(path), fy=fy, rev_table=rev_t[0]["start"], cost_table=cost_t[0]["start"], unit=unit)
    # period marker: the prior tables are announced by a '전반기|전분기' mini table right before them; also the ACONTEXT of the first numeric cell for the XBRL dialect
    ra = pick(rrr, c["ra"]); csm = pick(rrr, c["csm"]); exp = pick(rrr, c["exp"], exclude=("기타",)); exp2 = pick(rrr, c["exp2"])
    acq = pick(rrr, c["acq"]); loss = pick(rrr, c["loss"])
    tot_rev = [x for x in rrr if x["key"] == c["total_rev"]][-1]
    act = pick(ccc, c["act"], exclude=("기타",)); act2 = pick(ccc, c["act2"])
    rec["rev_rows"] = dict(ra=ra, csm=csm, exp=exp, exp2=exp2, acq=acq, loss=loss, total=tot_rev)
    if q == "2024.2Q":
        lc, ib, ca, cl = pick(ccc, c["c_loss_contract"]), pick(ccc, c["c_ibnr"]), pick(ccc, c["c_acq"]), pick(ccc, c["c_lossalloc"])
        oth = [x for x in ccc if x["key"].endswith("기타") or x["key"] == "기타"][-1]
        tot_cost = [x for x in ccc if "발행한보험계약에서생기는보험서비스비용" in x["key"] and "실제" not in x["key"]][0]
        other_cost = [act2, lc, ib, ca, cl, oth]
    else:
        fut, pas, ca, cl = pick(ccc, c["c_future"]), pick(ccc, c["c_past"]), pick(ccc, c["c_acq"]), pick(ccc, c["c_lossalloc"])
        oth = pick(ccc, c["c_other"])
        tot_cost = [x for x in ccc if x["key"] == c["total_cost"]][0]
        other_cost = [act2, fut, pas, ca, cl, oth]
    rec["cost_rows"] = dict(act=act, act2=act2, total=tot_cost, others=[x["key"] for x in other_cost])
    rec["cost_other_rows"] = other_cost
    AB = lambda x: abs(x["cum"]["v"])  # noqa: E731
    v5, v4 = AB(ra), AB(csm)
    v6 = abs(exp["cum"]["v"]) - abs(act["cum"]["v"])
    rec["items"] = {"4": v4, "5": v5, "6": v6}
    rec["items_3m"] = {"4": abs(csm["m3"]["v"]), "5": abs(ra["m3"]["v"]), "6": abs(exp["m3"]["v"]) - abs(act["m3"]["v"])}
    rev_other = [exp2, acq, loss]
    s_rev = sum(x["cum"]["v"] for x in (exp, exp2, ra, csm, acq, loss))
    s_cost = sum(x["cum"]["v"] for x in [act] + other_cost)
    rec["closure_rows"] = dict(rev_sum=s_rev, rev_total=tot_rev["cum"]["v"], cost_sum=s_cost, cost_total=tot_cost["cum"]["v"])
    m = {i: live.get((q, i), {}).get("값") for i in (3, 4, 5, 6, 7)}
    rec["master"] = m
    i7 = m[3] - (m[4] + v5 + v6)
    other7 = sum(x["cum"]["v"] for x in rev_other) - sum(x["cum"]["v"] for x in other_cost)
    rec["i7"] = i7
    rec["other7"] = other7
    rec["rev_other_rows"] = rev_other
    other7_3m = sum(x["m3"]["v"] for x in rev_other) - sum(x["m3"]["v"] for x in other_cost)
    rec["other7_3m"] = other7_3m
    res[q] = rec
    PR(f"##### {q} <- {fy} {rec['file']} rev@L{rev_t[0]['start']} cost@L{cost_t[0]['start']} (prior-period tables, separate, {unit})")
    PR(f"  5 = {v5:,.0f} (RA 누적 {ra['cum']['text']}@L{ra['cum']['line']}, 3M {ra['m3']['text']}@L{ra['m3']['line']})   4 = {v4:,.0f} (CSM {csm['cum']['text']}@L{csm['cum']['line']})")
    PR(f"  6 = {v6:,.0f} = 예상 {exp['cum']['text']}@L{exp['cum']['line']} - 실제 {act['cum']['text']}@L{act['cum']['line']}  (3M: {exp['m3']['text']} - {act['m3']['text']} = {rec['items_3m']['6']:,.0f})")
    PR(f"  master: 4={m[4]} 5={m[5]} 6={m[6]} | 3={m[3]} 7={m[7]}")
    PR(f"  closure: revenue rows {s_rev:,.0f} vs printed total {tot_rev['cum']['v']:,.0f} ; cost rows {s_cost:,.0f} vs printed total {tot_cost['cum']['v']:,.0f}")
    PR(f"  derived 7 = {i7:,.6f} vs other rows {other7:,.0f} (diff {i7 - other7:+.3f}); 3M other rows = {other7_3m:,.0f}")
json.dump(res, open(f"{EVD}/r01_dy_read.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(f"{EVD}/r01_dy_read.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out_txt) + "\n")
