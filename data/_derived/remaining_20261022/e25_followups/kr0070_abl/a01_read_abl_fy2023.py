# -*- coding: utf-8 -*-
"""READ-ONLY (ticket 20261023T1210Z, KR0070 ABL FY2023 2023.1Q-2023.4Q): read the restated comparative (prior-period cumulative column of the FY2024 Q1/H1/Q3/annual filings, separate-basis notes)
of the 보험영업수익 / 보험영업비용 note tables and derive PL items 4, 5, 6, 9, 10, 11 with the production definitions (extract_tier2_abl):
  4  = 보험수익 section 보험계약마진상각                      5  = 보험수익 section 위험조정변동
  6  = (예상보험금+예상손해조사비+예상계약유지비+예상투자관리비) - (발생보험금+발생손해조사비+발생계약유지비+발생투자관리비)
  9  = -|재보험비용 section 보험계약마진상각|                10 = -|재보험비용 section 위험조정변동|
  11 = (발생재보험금+발생손해조사비 [재보험수익 section]) - (예상재보험금+예상손해조사비 [재보험비용 section])
Cross-checks printed here: (a) section subtotals (소계) = sum of the rows of the same column; (b) the same CSM / RA amounts in the prior-period measurement roll-forward tables
(insurance contracts and reinsurance contracts); (c) single-quarter seam: derived (cum_q - cum_q-1) vs the printed prior 3-month column (H1 / Q3 filings).
Output: a01_read_abl_fy2023.json (values with citations), a01_read_abl_fy2023.txt (human view)."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl")
import e23_read as E  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
M, T, W = E.M, E.T, E.W
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/kr0070_abl"
QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]
FY = {"2023.1Q": "FY2024_Q1", "2023.2Q": "FY2024_Q2", "2023.3Q": "FY2024_Q3", "2023.4Q": "FY2024_Q4"}
SECTIONS = ("보험수익", "재보험수익", "보험서비스비용", "재보험비용")


def nums(row):
    """numeric cells after the label: [(val, line, text)] ('-' = 0)"""
    out = []
    for c in row["cells"][1:]:
        if c["val"] is not None:
            out.append((c["val"], c["line"], c["text"]))
        elif c["text"].strip() in ("-", "\u2212"):
            out.append((0.0, c["line"], c["text"]))
    return out


def walk(rows):
    """{section: {label: nums}} (labels normalised, first occurrence wins), plus ordered section list"""
    sec, out = None, {}
    for r in rows:
        if not r["cells"]:
            continue
        lab = E.lab(r)
        n = nums(r)
        if not n and lab in SECTIONS:
            sec = lab
            out.setdefault(sec, {})
            continue
        if sec is None:
            if lab in ("기타사업비용", "합계"):
                out.setdefault("_tail", {}).setdefault(lab, n)
            continue
        out[sec].setdefault(lab, n)
        if lab in ("기타사업비용", "합계"):
            out.setdefault("_tail", {}).setdefault(lab, n)
    return out


def pick(tabs, pred, what, path):
    hits = [(t, rows) for t, rows in tabs if pred([E.lab(r) for r in rows])]
    if len(hits) != 1:
        raise RuntimeError(f"{path.name}: {len(hits)} {what} tables (need 1): {[h[0]['start'] for h in hits]}")
    return hits[0]


def rf_tables(tabs):
    """prior-period measurement roll-forward tables '2) 전분기|전반기|전기' (insurance: I.기초보험계약순부채 / reinsurance: I.기초재보험계약순자산(부채)) with columns [최선추정, 위험조정, 보험계약마진, 합계]"""
    ins = rein = None
    for t, rows in tabs:
        cap = E.nl(t["caption"] or "")
        if not re.match(r"^2\)(전분기|전반기|전기)$", cap):
            continue
        hdr = E.nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        if "최선추정" not in hdr or "위험조정" not in hdr:
            continue
        labs = [E.lab(r) for r in rows]
        if any(x.startswith("I.기초보험계약순부채") for x in labs):
            ins = (t, rows) if ins is None else "DUP"
        if any(x.startswith("I.기초재보험계약순자산") for x in labs):
            rein = (t, rows) if rein is None else "DUP"
    return ins, rein


def rf_val(rows, prefix, col):
    for r in rows:
        if E.lab(r).startswith(prefix):
            n = nums(r)
            return n[col][0], n[col][1], n[col][2]
    raise RuntimeError(f"roll-forward row {prefix!r} not found")


live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0070"}
res, lines_out = {}, []


def P(s=""):
    print(s)
    lines_out.append(s)


for q in QS:
    path = T.main_path("KR0070", FY[q])
    lines, s0, tabs = E.tables_sep(path)
    rev_t, rev_rows = pick(tabs, lambda L: "예상보험금" in L and "소계" in L and "재보험수익" in L and "보험계약마진상각" in L and "위험조정변동" in L, "보험영업수익", path)
    cost_t, cost_rows = pick(tabs, lambda L: "발생보험금" in L and "예상재보험금" in L and "기타사업비용" in L, "보험영업비용", path)
    unit = T.find_unit(lines, rev_t, span=2500)
    unit_c = T.find_unit(lines, cost_t, span=2500)
    rv, cv = walk(rev_rows), walk(cost_rows)
    n_cols = len(rv["보험수익"]["예상보험금"])
    # column positions: Q1/Q4 [cur, prior] ; Q2/Q3 [cur3m, curcum, prior3m, priorcum]
    PRIOR_CUM = n_cols - 1
    PRIOR_3M = 2 if n_cols == 4 else (0 if n_cols == 2 and q == "2023.1Q" else None)

    def g(d, sec, label, col):
        n = d[sec].get(label)
        if n is None:
            return None
        return n[col]  # (val, line, text)

    def cell(d, sec, label, col):
        c = g(d, sec, label, col)
        return None if c is None else (c[0], c[1], c[2])

    out = dict(file=M.rel(path), fy=FY[q], rev_table=rev_t["start"], cost_table=cost_t["start"], unit=unit, unit_cost=unit_c, n_cols=n_cols, cites={})
    P(f"##### {q} <- {FY[q]} {out['file']}  rev table@L{rev_t['start']} cost table@L{cost_t['start']} unit {unit}/{unit_c} columns/row {n_cols}")
    assert unit == "백만원" and unit_c == "백만원", "unexpected unit"

    def col_vals(col):
        """all items for one column index"""
        v = {}
        v[4] = cell(rv, "보험수익", "보험계약마진상각", col)
        v[5] = cell(rv, "보험수익", "위험조정변동", col)
        exp = [cell(rv, "보험수익", k, col) for k in ("예상보험금", "예상손해조사비", "예상계약유지비", "예상투자관리비")]
        inc = [cell(cv, "보험서비스비용", k, col) for k in ("발생보험금", "발생손해조사비", "발생계약유지비", "발생투자관리비")]
        v["exp4"], v["inc4"] = exp, inc
        assert exp[0] is not None and inc[0] is not None, "claim rows missing"
        v[6] = sum(c[0] for c in exp if c) - sum(c[0] for c in inc if c)
        v[9] = cell(cv, "재보험비용", "보험계약마진상각", col)
        v[10] = cell(cv, "재보험비용", "위험조정변동", col)
        rinc = [cell(rv, "재보험수익", k, col) for k in ("발생재보험금", "발생손해조사비")]
        rexp = [cell(cv, "재보험비용", k, col) for k in ("예상재보험금", "예상손해조사비")]
        v["rinc2"], v["rexp2"] = rinc, rexp
        assert rinc[0] is not None and rexp[0] is not None, "reinsurance claim rows missing"
        v[11] = sum(c[0] for c in rinc if c) - sum(c[0] for c in rexp if c)
        # subtotal checks
        chk = {}
        for name, d, sec in (("보험수익", rv, "보험수익"), ("재보험수익", rv, "재보험수익"), ("보험서비스비용", cv, "보험서비스비용"), ("재보험비용", cv, "재보험비용")):
            rows_ = {k: x for k, x in d[sec].items() if k not in ("소계", "합계", "기타사업비용")}
            s = sum(x[col][0] for x in rows_.values())
            chk[name] = (s, d[sec]["소계"][col][0], len(rows_))
        v["subtotals"] = chk
        v["tail"] = {k: x[col][0] for k, x in rv.get("_tail", {}).items()} | {("cost_" + k): x[col][0] for k, x in cv.get("_tail", {}).items()}
        return v

    vp = col_vals(PRIOR_CUM)
    vc = col_vals(1 if n_cols == 4 else 0)
    out["prior_cum"] = {k: vp[k] for k in (4, 5, 6, 9, 10, 11)}
    out["prior_cum_cites"] = {k: vp[k] for k in ("exp4", "inc4", "rinc2", "rexp2")}
    out["subtotal_check_prior"] = vp["subtotals"]
    out["cur_cum"] = {k: vc[k] for k in (4, 5, 6, 9, 10, 11)}
    out["tail_prior"] = vp["tail"]
    if PRIOR_3M is not None and n_cols == 4:
        v3 = col_vals(PRIOR_3M)
        out["prior_3m"] = {k: v3[k] for k in (4, 5, 6, 9, 10, 11)}
        out["subtotal_check_prior_3m"] = v3["subtotals"]
    # roll-forward cross-check
    ins, rein = rf_tables(tabs)
    rfx = {}
    if ins and ins != "DUP":
        t, rows = ins
        rfx["ins_csm_release"] = rf_val(rows, "(1)서비스제공으로당기손익으로인식된보험계약마진", 2)
        rfx["ins_ra_release"] = rf_val(rows, "(2)비금융위험에대한위험조정변동", 1)
        rfx["ins_table"] = t["start"]
    else:
        rfx["ins_table"] = ins
    if rein and rein != "DUP":
        t, rows = rein
        rfx["rein_csm_release"] = rf_val(rows, "(1)서비스제공으로당기손익으로인식된보험계약마진", 2)
        rfx["rein_ra_release"] = rf_val(rows, "(2)비금융위험에대한위험조정변동", 1)
        rfx["rein_table"] = t["start"]
    else:
        rfx["rein_table"] = rein
    out["rollforward"] = rfx

    P(f"  prior-period CUMULATIVE (restated comparative), 백만원:")
    for it in (4, 5, 9, 10):
        c = vp[it]
        P(f"    item {it:>2}: {c[0]:>10.0f}  (printed {c[2]!r} @L{c[1]})    live master {live.get((q, it), {}).get('값')}")
    P(f"    item  6: {vp[6]:>10.0f}  = 예상4 {[x[0] if x else 0 for x in vp['exp4']]} - 발생4 {[x[0] if x else 0 for x in vp['inc4']]} (lines {[x[1] if x else None for x in vp['exp4']]} / {[x[1] if x else None for x in vp['inc4']]})    live master {live.get((q, 6), {}).get('값')}")
    P(f"    item 11: {vp[11]:>10.0f}  = 발생재보험 {[x[0] if x else 0 for x in vp['rinc2']]} - 예상재보험 {[x[0] if x else 0 for x in vp['rexp2']]}    live master {live.get((q, 11), {}).get('값')}")
    P(f"    subtotal check (sum rows vs printed 소계): " + "; ".join(f"{k}: {a:.0f} vs {b:.0f} ({n} rows) {'OK' if abs(a - b) <= 1.5 else 'DIFF'}" for k, (a, b, n) in vp["subtotals"].items()))
    P(f"    tail (기타사업비용/합계): {vp['tail']}")
    P(f"    roll-forward cross-check: " + json.dumps({k: (v if not isinstance(v, tuple) else [v[0], v[1]]) for k, v in rfx.items()}, ensure_ascii=False))
    if "prior_3m" in out:
        P("    prior 3-month column (printed): " + "; ".join(f"item{k}={out['prior_3m'][k] if k == 6 or k == 11 else out['prior_3m'][k][0]}" for k in (4, 5, 6, 9, 10, 11)))
    res[q] = out
    res[q]["_vp"] = {k: (vp[k] if isinstance(vp[k], (int, float)) else list(vp[k])) for k in (4, 5, 6, 9, 10, 11)}


def val(x):
    return x if isinstance(x, (int, float)) else x[0]


# ---- derived single quarters vs printed prior 3-month columns (H1 / Q3 filings)
P("\n##### single-quarter seam: derived (cum_q - cum_q-1, both from the restated comparatives) vs printed prior 3-month column")
SIGN = {4: 1, 5: 1, 6: 1, 9: -1, 10: -1, 11: 1}  # adopted sign convention: item9/10 = -|value|
for q, pq in (("2023.2Q", "2023.1Q"), ("2023.3Q", "2023.2Q")):
    for it in (4, 5, 6, 9, 10, 11):
        cum_q, cum_p = val(res[q]["prior_cum"][it]), val(res[pq]["prior_cum"][it])
        p3 = val(res[q]["prior_3m"][it])
        d = cum_q - cum_p
        P(f"  {q} item {it:>2}: derived {d:>9.0f} (= {cum_q:.0f} - {cum_p:.0f}) vs printed 3m {p3:>9.0f}  diff {d - p3:+.0f}")
json.dump({k: {kk: vv for kk, vv in v.items() if kk != "_vp"} for k, v in res.items()}, open(f"{EV}/a01_read_abl_fy2023.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
open(f"{EV}/a01_read_abl_fy2023.txt", "w", encoding="utf-8").write("\n".join(lines_out) + "\n")
