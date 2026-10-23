# -*- coding: utf-8 -*-
"""READ-ONLY pass3 r10 (KR0070 ABL, ticket 20261024T0600Z item 1).  Reads the separate-basis 보험영업수익 / 보험영업비용 note tables of the filing of each quarter itself (2025.3Q = FY2025_Q3 ...
2026.2Q = FY2026_Q2: no later fiscal-year filing exists yet, so the CURRENT-period column is the latest) and derives the PL items with the production definitions (same as pass2 r03):
  4 = 보험수익 구간 보험계약마진상각              5 = 보험수익 구간 위험조정변동
  6 = (예상보험금+예상손해조사비+예상계약유지비+예상투자관리비) - (발생보험금+발생손해조사비+발생계약유지비+발생투자관리비)
  9 = -|재보험비용 구간 보험계약마진상각|         10 = -|재보험비용 구간 위험조정변동|
  11 = (발생재보험금+발생손해조사비 [재보험수익 구간]) - (예상재보험금+예상손해조사비 [재보험비용 구간])
  7 = 3 - (4+5+6)   12 = 8 - (9+10+11)   (3, 8 = live master values)
Columns: Q1/Q4 filings carry 2 numeric columns [당기, 전기] -> current = col 0 (cumulative); Q2/Q3 filings carry 4 [당분기(3M), 당기 누적, 전분기(3M), 전기 누적] -> current 3M = col 0, current cum = col 1.
Printed per quarter: (a) every 소계 = sum of its section rows, (b) item 3 / item 8 of the master vs the note subtotals, (c) item 7 / 12 vs the sum of the OTHER note rows (closure against the note itself),
(d) CSM / RA amounts vs the 당기 roll-forward of the same filing, (e) the printed 3-month column (Q2/Q3 filings) for the single-quarter seam.
Output: r10_abl_cur_read.json (values with physical xml line citations), r10_abl_cur_read.txt."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
E, T, M = P.E, P.T, P.M
EVD = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/kr0070_abl"
CODE = "KR0070"
TARGETS = {"2025.3Q": "FY2025_Q3", "2025.4Q": "FY2025_Q4", "2026.1Q": "FY2026_Q1", "2026.2Q": "FY2026_Q2"}
SECTIONS = ("보험수익", "재보험수익", "보험서비스비용", "재보험비용")
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{P.ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == CODE}


def cellrec(c):
    return None if c is None else dict(v=c[0], line=c[1], text=c[2])


def walk(rows):
    """{section: {label: [nums]}} (first occurrence wins), plus the ordered label list per section"""
    sec, out, order = None, {}, {}
    for r in rows:
        if not r["cells"]:
            continue
        lab = P.lab(r)
        n = P.nums(r)
        if not n and lab in SECTIONS:
            sec = lab
            out.setdefault(sec, {})
            order.setdefault(sec, [])
            continue
        if sec is None:
            continue
        if lab in ("기타사업비용", "합계"):
            out.setdefault("_tail", {}).setdefault(lab, n)
            continue
        if lab not in out[sec]:
            out[sec][lab] = n
            order[sec].append(lab)
    return out, order


def pick(tabs, pred, what, path):
    hits = [(t, rows) for t, rows in tabs if pred([P.lab(r) for r in rows])]
    if len(hits) != 1:
        raise RuntimeError(f"{path.name}: {len(hits)} {what} tables (need 1): {[h[0]['start'] for h in hits]}")
    return hits[0]


def rf_tables(tabs):
    ins = rein = None
    for t, rows in tabs:
        cap = P.nl(t["caption"] or "")
        if not re.match(r"^1\)(당분기|당반기|당기)$", cap):
            continue
        hdr = P.nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        if "최선추정" not in hdr or "위험조정" not in hdr:
            continue
        labs = [P.lab(r) for r in rows]
        if any(x.startswith("I.기초보험계약순부채") for x in labs):
            ins = (t, rows) if ins is None else "DUP"
        if any(x.startswith("I.기초재보험계약순자산") for x in labs):
            rein = (t, rows) if rein is None else "DUP"
    return ins, rein


def rf_val(rows, prefix, col):
    for r in rows:
        if P.lab(r).startswith(prefix):
            n = P.nums(r)
            return n[col]
    raise RuntimeError(f"roll-forward row {prefix!r} not found")


res, out_txt = {}, []


def PR(s=""):
    print(s)
    out_txt.append(s)


cache = {}
for q, fy in TARGETS.items():
    if fy not in cache:
        cache[fy] = P.load(CODE, fy)
    path, lines, s0, tabs = cache[fy]
    rev_t, rev_rows = pick(tabs, lambda L: "예상보험금" in L and "소계" in L and "재보험수익" in L and "보험계약마진상각" in L and "위험조정변동" in L, "보험영업수익", path)
    cost_t, cost_rows = pick(tabs, lambda L: "발생보험금" in L and "예상재보험금" in L and "기타사업비용" in L, "보험영업비용", path)
    unit = T.find_unit(lines, rev_t, span=2500)
    unit_c = T.find_unit(lines, cost_t, span=2500)
    assert unit == "백만원" and unit_c == "백만원", (q, unit, unit_c)
    rv, ro = walk(rev_rows)
    cv, co = walk(cost_rows)
    n_cols = len(rv["보험수익"]["예상보험금"])
    assert n_cols in (2, 4), n_cols
    CUR_CUM = 1 if n_cols == 4 else 0
    CUR_3M = 0 if n_cols == 4 else None
    rec = dict(file=M.rel(path), fy=fy, rev_table=rev_t["start"], cost_table=cost_t["start"], unit=unit, n_cols=n_cols, cur_cum_col=CUR_CUM)

    def vec(col):
        v = {}
        v["rev"] = {k: cellrec(n[col]) for k, n in rv["보험수익"].items()}
        v["re_rev"] = {k: cellrec(n[col]) for k, n in rv["재보험수익"].items()}
        v["cost"] = {k: cellrec(n[col]) for k, n in cv["보험서비스비용"].items()}
        v["re_cost"] = {k: cellrec(n[col]) for k, n in cv["재보험비용"].items()}
        return v

    def sub_check(v):
        out = {}
        for name, d in (("보험수익", v["rev"]), ("재보험수익", v["re_rev"]), ("보험서비스비용", v["cost"]), ("재보험비용", v["re_cost"])):
            rows_ = {k: x for k, x in d.items() if k != "소계"}
            s = sum(x["v"] for x in rows_.values())
            out[name] = (s, d["소계"]["v"], len(rows_))
        return out

    vp = vec(CUR_CUM)
    rec["cur_cum"] = vp
    rec["subtotal_check_cur_cum"] = sub_check(vp)
    if CUR_3M is not None:
        v3 = vec(CUR_3M)
        rec["cur_3m"] = v3
        rec["subtotal_check_cur_3m"] = sub_check(v3)
    # roll-forward cross-check (current-period tables)
    ins, rein = rf_tables(tabs)
    rfx = {}
    try:
        if ins and ins != "DUP":
            t, rows = ins
            rfx["ins_csm_release"] = cellrec(rf_val(rows, "(1)서비스제공으로당기손익으로인식된보험계약마진", 2))
            rfx["ins_ra_release"] = cellrec(rf_val(rows, "(2)비금융위험에대한위험조정변동", 1))
            rfx["ins_table"] = t["start"]
        if rein and rein != "DUP":
            t, rows = rein
            rfx["rein_csm_release"] = cellrec(rf_val(rows, "(1)서비스제공으로당기손익으로인식된보험계약마진", 2))
            rfx["rein_ra_release"] = cellrec(rf_val(rows, "(2)비금융위험에대한위험조정변동", 1))
            rfx["rein_table"] = t["start"]
    except RuntimeError as exc:
        rfx["error"] = str(exc)
    rfx["ins_status"] = "DUP" if ins == "DUP" else ("none" if not ins else "ok")
    rfx["rein_status"] = "DUP" if rein == "DUP" else ("none" if not rein else "ok")
    rec["rollforward_cur"] = rfx

    A = lambda x: abs(x["v"])  # noqa: E731

    def derive(vv, masterkey):
        r_, c_, rr, rc = vv["rev"], vv["cost"], vv["re_rev"], vv["re_cost"]
        exp4 = [r_.get(k) for k in ("예상보험금", "예상손해조사비", "예상계약유지비", "예상투자관리비")]
        inc4 = [c_.get(k) for k in ("발생보험금", "발생손해조사비", "발생계약유지비", "발생투자관리비")]
        it = {}
        it[4] = r_["보험계약마진상각"]["v"]
        it[5] = r_["위험조정변동"]["v"]
        it[6] = sum(x["v"] for x in exp4 if x) - sum(x["v"] for x in inc4 if x)
        it[9] = -A(rc["보험계약마진상각"])
        it[10] = -A(rc["위험조정변동"])
        ract = [rr.get(k) for k in ("발생재보험금", "발생손해조사비")]
        rexp = [rc.get(k) for k in ("예상재보험금", "예상손해조사비")]
        it[11] = sum(x["v"] for x in ract if x) - sum(x["v"] for x in rexp if x)
        rev_other = [k for k in r_ if k not in ("예상보험금", "예상손해조사비", "예상계약유지비", "예상투자관리비", "위험조정변동", "보험계약마진상각", "소계")]
        cost_other = [k for k in c_ if k not in ("발생보험금", "발생손해조사비", "발생계약유지비", "발생투자관리비", "소계")]
        other7 = sum(r_[k]["v"] for k in rev_other) - sum(c_[k]["v"] for k in cost_other)
        rr_other = [k for k in rr if k not in ("발생재보험금", "발생손해조사비", "소계")]
        rc_other = [k for k in rc if k not in ("예상재보험금", "예상손해조사비", "위험조정변동", "보험계약마진상각", "소계")]
        other12 = sum(rr[k]["v"] for k in rr_other) - sum(rc[k]["v"] for k in rc_other)
        sub = {"rev": vv["rev"]["소계"]["v"], "cost": vv["cost"]["소계"]["v"], "re_rev": vv["re_rev"]["소계"]["v"], "re_cost": vv["re_cost"]["소계"]["v"]}
        return it, dict(rev_other=rev_other, cost_other=cost_other, other7=other7, rr_other=rr_other, rc_other=rc_other, other12=other12, sub=sub, ract=ract, rexp=rexp, exp4=exp4, inc4=inc4)

    it, aux = derive(vp, "cum")
    m = {i: live.get((q, i), {}).get("값") for i in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12)}
    rec["master"] = m
    rec["items"] = {str(k): v for k, v in it.items()}
    # derived 7 / 12 with the master operands 3 / 8 and the MASTER item 4 when it exists (gold), else the note value
    new4 = m[4] if m[4] is not None else it[4]
    i7 = m[3] - (new4 + it[5] + it[6])
    i12 = m[8] - (it[9] + it[10] + it[11])
    rec["items"]["7"], rec["items"]["12"] = i7, i12
    rec["aux"] = {k: (v if not isinstance(v, list) or not v or not isinstance(v[0], dict) else v) for k, v in aux.items()}
    rec["closure7"] = dict(rev_other=aux["rev_other"], cost_other=aux["cost_other"], value=aux["other7"], derived=i7, diff=i7 - aux["other7"])
    rec["closure12"] = dict(rr_other=aux["rr_other"], rc_other=aux["rc_other"], value=aux["other12"], derived=i12, diff=i12 - aux["other12"])
    sub = rec["subtotal_check_cur_cum"]
    rec["i3_note"] = sub["보험수익"][1] - sub["보험서비스비용"][1]
    rec["i8_note"] = sub["재보험수익"][1] - sub["재보험비용"][1]
    if CUR_3M is not None:
        it3, aux3 = derive(rec["cur_3m"], "3m")
        rec["items_3m"] = {str(k): v for k, v in it3.items()}
        rec["other7_3m"], rec["other12_3m"] = aux3["other7"], aux3["other12"]
        rec["sub_3m"] = aux3["sub"]
    res[q] = rec

    PR(f"##### {q} <- {fy} {rec['file']} (rev@L{rev_t['start']} cost@L{cost_t['start']}, {n_cols} numeric cols, cur cum = col {CUR_CUM})")
    PR(f"  items (note, cur cum): 4={it[4]:.0f}@L{vp['rev']['보험계약마진상각']['line']} 5={it[5]:.0f}@L{vp['rev']['위험조정변동']['line']} 6={it[6]:.0f} 9={it[9]:.0f}@L{vp['re_cost']['보험계약마진상각']['line']} 10={it[10]:.0f}@L{vp['re_cost']['위험조정변동']['line']} 11={it[11]:.0f}")
    PR(f"  master:               4={m[4]} 5={m[5]} 6={m[6]} 9={m[9]} 10={m[10]} 11={m[11]} | 3={m[3]} 7={m[7]} 8={m[8]} 12={m[12]}")
    PR("  subtotals (sum rows vs printed): " + "; ".join(f"{k}: {a:.0f} vs {b:.0f} ({n}) {'OK' if abs(a - b) <= 1.5 else 'DIFF'}" for k, (a, b, n) in sub.items()))
    PR(f"  3: master {m[3]:.3f} vs note (보험수익 소계-보험서비스비용 소계) {rec['i3_note']:.0f}; 8: master {m[8]:.3f} vs note {rec['i8_note']:.0f}")
    PR(f"  derived 7 = {i7:.3f}  vs other-rows sum {aux['other7']:.0f} (diff {i7 - aux['other7']:+.3f}) | rows rev {aux['rev_other']} cost {aux['cost_other']}")
    PR(f"  derived 12 = {i12:.3f} vs other-rows sum {aux['other12']:.0f} (diff {i12 - aux['other12']:+.3f}) | rows re_rev {aux['rr_other']} re_cost {aux['rc_other']}")
    PR("  roll-forward (cur table): " + "; ".join(f"{k}={v['v']:.0f}@L{v['line']}" for k, v in rfx.items() if isinstance(v, dict)) + f" | status ins={rfx['ins_status']} rein={rfx['rein_status']}" + (f" ERR {rfx['error']}" if "error" in rfx else ""))
    if CUR_3M is not None:
        PR(f"  printed cur 3M items: " + " ".join(f"{k}={v:.0f}" for k, v in rec["items_3m"].items()) + f" | 3M other7 {rec['other7_3m']:.0f} other12 {rec['other12_3m']:.0f}")

json.dump(res, open(f"{EVD}/r10_abl_cur_read.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
open(f"{EVD}/r10_abl_cur_read.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out_txt) + "\n")
