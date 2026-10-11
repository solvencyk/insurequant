# -*- coding: utf-8 -*-
"""Extension of the Lina Life (KR0074) CSM backfill to the remaining eight quarters 2023.1Q .. 2025.2Q (owner: ALL quarters).

Called by scripts/extract_lina_csm_rows_20261011.py (which stages the three first quarters).  Nothing is written here; the function
run() returns rows + a report and the caller writes the staging files.  Master files are only READ.

Method (same proofs as the first three quarters):
  * for every quarter the OWN-period column of its filing and the PRIOR-period column of the next year's filing(s) are read with the
    x-coordinate reader (_lina_csm_tables_20261011.py); every page must close (exact in the CSM columns for the restated-basis formats);
  * own vs later column: equal within TOL_PRINT 천원 = no conflict -> the own print is adopted; otherwise the repo rule "latest
    disclosure prior-column wins" adopts the later print;
  * the adopted print must continue the master: opening == master previous year-end close (2024, 2025), == the master 2023.4Q opening
    (2023: the restated 2023.1.1 balance); a print that fails this (printed only on the old, pre-restatement basis) is a HOLD, not forced;
  * within-FY openings equal, YTD flows monotone through the master year-end row, quarter-only new CSM >= 0, close == ILP master item 3;
  * amortisation schedules: yearly format -> 10 rows each (staged for the later amortisation load); coarse 5-bucket format -> staged
    separately (the master schema is yearly); old basis -> hold.
"""
from __future__ import annotations

import json
from pathlib import Path

import fitz

import _lina_csm_tables_20261011 as R
from _disclosure_pdf_paths import latest_disclosure_pdfs

ROOT = Path(__file__).resolve().parents[1]
CODE = "KR0074"
EOK = 100_000
TOL_PRINT = 3                       # 천원: own print vs later prior column (rounding of single table vs two accounts summed)
YE_CTX = ("2023.4Q", "2024.4Q", "2025.4Q")      # the year-end rows the master held before any quarterly row of Lina was loaded
SIX = ("open", "new", "fin", "adj", "amort", "close")
CSM_ITEM_NM = {1: "기초 CSM", 2: "신계약 CSM", 3: "이자 부리", 4: "가정 및 경험 조정", 5: "CSM 상각", 6: "기말 CSM"}

# quarter, as_of, own filing + pages + marker, later filing(s) + pages + marker, old-format flag (5/7-column pre-restatement print possible)
PLAN = [
    {"q": "2023.1Q", "as_of": "2023-03-31", "own": ("FY2023_Q1", {"전사": 57}, "<당분기>"), "later": ("FY2024_Q1", {"전사": 52}, "<전분기>"), "old": True},
    {"q": "2023.2Q", "as_of": "2023-06-30", "own": ("FY2023_Q2", {"전사": 84}, "<당반기>"), "later": ("FY2024_Q2", {"전사": 77}, "<전반기>"), "old": True},
    {"q": "2023.3Q", "as_of": "2023-09-30", "own": ("FY2023_Q3", {"전사": 62}, "<당분기>"), "later": ("FY2024_Q3", {"전사": 53}, "<전분기>"), "old": True},
    {"q": "2024.1Q", "as_of": "2024-03-31", "own": ("FY2024_Q1", {"전사": 51}, "<당분기>"), "later": ("FY2025_Q1", {"전사": 58}, "<전분기>"), "old": False},
    {"q": "2024.2Q", "as_of": "2024-06-30", "own": ("FY2024_Q2", {"전사": 76}, "<당반기>"), "later": ("FY2025_Q2", {"전사": 84}, "<전반기>"), "old": False},
    {"q": "2024.3Q", "as_of": "2024-09-30", "own": ("FY2024_Q3", {"전사": 52}, "<당분기>"), "later": ("FY2025_Q3", {"전사": 64}, "<전분기>"), "old": False},
    {"q": "2025.1Q", "as_of": "2025-03-31", "own": ("FY2025_Q1", {"전사": 57}, "<당분기>"), "later": ("FY2026_Q1", {"유배당": 67, "유배당 외": 69}, "<전분기>"), "old": False},
    {"q": "2025.2Q", "as_of": "2025-06-30", "own": ("FY2025_Q2", {"전사": 83}, "<당반기>"), "later": ("FY2026_Q2", {"유배당": 92, "유배당 외": 94}, "<전반기>"), "old": False},
]
AMORT_YEARLY = {"2025.1Q": ("FY2025_Q1", 60), "2025.2Q": ("FY2025_Q2", 86)}
AMORT_COARSE = {"2024.1Q": ("FY2024_Q1", 54), "2024.2Q": ("FY2024_Q2", 79), "2024.3Q": ("FY2024_Q3", 55)}
AMORT_OLD_BASIS = {"2023.1Q": ("FY2023_Q1", 61), "2023.2Q": ("FY2023_Q2", 88), "2023.3Q": ("FY2023_Q3", 65)}
COARSE_LABELS = ["1년 이내", "1년 초과 3년 이하", "3년 초과 5년 이하", "5년 초과 10년 이하", "10년 초과"]


def eok(x: int) -> float:
    return round(x / EOK, 5)


class _Docs:
    def __init__(self):
        self.d = {}

    def get(self, fy):
        if fy not in self.d:
            pdf = latest_disclosure_pdfs(fy, CODE)[0]
            self.d[fy] = (pdf, fitz.open(pdf))
        return self.d[fy]


def _read_set(docs, fy, pages: dict, marker: str, csm_tol: int):
    pdf, doc = docs.get(fy)
    per, items = {}, {}
    problems = []
    for acct, p in pages.items():
        pg = doc[p - 1]
        t = R.norm(pg.get_text())
        if marker not in t:
            problems.append(f"{fy} p{p}: marker {marker} not on the page")
        if "최초인식한계약의효과" not in t or "보험계약마진" not in t:
            problems.append(f"{fy} p{p}: not the roll-forward note")
        rd = R.read_note(pg)
        pr = R.check_note(rd, csm_tol=csm_tol)
        if pr:
            problems.append(f"{fy} p{p}: {pr[:2]}")
            continue
        it = R.csm_items(rd)
        per[acct] = {"page": p, "ncols": rd["ncols"], "items": it}
    if problems:
        return {"problems": problems}
    tot = R.sum_items({a: v["items"] for a, v in per.items()})
    return {"problems": [], "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "fy": fy, "pages": pages, "per_account": per,
            "items": tot, "residual": R.csm_residual(tot)}


def run(*, meta, m_val, cur_dangi, reg_tot, ytd_core, core_staged, BR) -> dict:
    docs = _Docs()
    rep = {"quarters": {}, "checks": [], "holds": [], "notes": []}
    ilp = {r["공시분기"]: r["값"] for r in json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
           if r["원보험사코드"] == CODE and r["항목번호"] == 3}

    # ------------------------------------------------------------------ 1. read both prints of every quarter, decide
    adopted = {}
    holds = {}
    for spec in PLAN:
        q = spec["q"]
        o_fy, o_pages, o_mark = spec["own"]
        l_fy, l_pages, l_mark = spec["later"]
        tol = 1 if spec["old"] else 0
        own = _read_set(docs, o_fy, o_pages, o_mark, tol)
        lat = _read_set(docs, l_fy, l_pages, l_mark, tol)
        if own["problems"] or lat["problems"]:
            # an old-basis page that only closes with a larger tolerance is reported, not loaded
            raise SystemExit(f"{q}: a source page does not close: own {own['problems']} later {lat['problems']}")
        diffs = {k: own["items"][k] - lat["items"][k] for k in SIX}
        conflict = any(abs(d) > TOL_PRINT for d in diffs.values())
        chosen, which = (lat, "later prior column (latest disclosure wins)") if conflict else (own, "own-period column")
        y = int(q[:4])
        exp_open = m_val[("2023.4Q", 1)] if y == 2023 else m_val[(f"{y - 1}.4Q", 6)]
        got_open = round(chosen["items"]["open"] / EOK, 1)
        continues = abs(got_open - exp_open) < 0.0501
        own_cont = abs(round(own["items"]["open"] / EOK, 1) - exp_open) < 0.0501
        lat_cont = abs(round(lat["items"]["open"] / EOK, 1) - exp_open) < 0.0501
        rec = {"own": {k: own[k] for k in ("pdf", "fy", "pages", "items", "residual")}, "later": {k: lat[k] for k in ("pdf", "fy", "pages", "items", "residual")},
               "own_minus_later_천원": diffs, "conflict": conflict, "adopted": which, "adopted_items_천원": chosen["items"],
               "expected_opening_억원(master)": exp_open, "adopted_opening_억원": round(chosen["items"]["open"] / EOK, 5),
               "own_continues_master": own_cont, "later_continues_master": lat_cont, "continues_master": continues,
               "adopted_residual_천원": chosen["residual"], "adopted_other_row_csm_천원": chosen["items"]["other"]}
        rep["quarters"][q] = rec
        if not continues:
            holds[q] = {"q": q, "reason": ("only printed on the old (pre-restatement) basis: opening %.5f 억원 != master %s opening %.1f 억원"
                                            % (chosen["items"]["open"] / EOK, "2023.4Q" if y == 2023 else f"{y - 1}.4Q close", exp_open)),
                        "own_continues": own_cont, "later_continues": lat_cont, "chosen": chosen, "which": which}
            continue
        if chosen["residual"] != 0 or chosen["items"]["other"] != 0:
            raise SystemExit(f"{q}: adopted print has residual {chosen['residual']} / other {chosen['items']['other']} -- would need a plug")
        adopted[q] = {"spec": spec, "chosen": chosen, "which": which, "conflict": conflict}
    rep["holds"] = [{k: v for k, v in h.items() if k != "chosen"} for h in holds.values()]
    n_pages = sum(len(s["own"][1]) + len(s["later"][1]) for s in PLAN)
    rep["checks"].append({"name": f"extension: every source page ({n_pages} pages = own + later columns of 8 quarters) closes: exact in the CSM columns for the "
                                  "restated-basis formats, printed 1-천원 rounding tolerated only on the old-basis pages", "pass": True})

    # ------------------------------------------------------------------ 2. chains: within-FY opening, YTD monotonicity, adjacency
    chain = {2023: {"2023.4Q": reg_tot["2023.4Q"]}, 2024: {"2024.4Q": reg_tot["2024.4Q"]}, 2025: {"2025.4Q": reg_tot["2025.4Q"], "2025.3Q": ytd_core["2025.3Q"]}}
    for q, a in adopted.items():
        chain[int(q[:4])][q] = a["chosen"]["items"]
    chain_rep, ok_chain = {}, True
    for y, qs in chain.items():
        order = sorted(qs)
        ref_open = qs[f"{y}.4Q"]["open"]
        opens = {q: qs[q]["open"] - ref_open for q in order}
        open_ok = all(abs(d) <= 5 for d in opens.values())
        mono = {}
        for k, sign in (("new", 1), ("fin", 1), ("amort", -1)):
            seq = [sign * qs[q][k] for q in order]
            mono[k] = {"seq_억원": [round(sign * v / EOK, 2) for v in seq], "monotone": all(b >= a for a, b in zip(seq, seq[1:]))}
        chain_rep[str(y)] = {"quarters": order, "opening_minus_year_end_opening_천원": opens, "openings_equal": open_ok, "ytd_flows": mono}
        ok_chain &= open_ok and all(m["monotone"] for m in mono.values())
    rep["chains"] = chain_rep
    rep["checks"].append({"name": "within-FY openings equal (+-5 천원) and YTD 신계약/이자/상각 monotone through the master year-end row", "pass": ok_chain})
    if not ok_chain:
        raise SystemExit("chain checks failed: " + json.dumps(chain_rep, ensure_ascii=False)[:600])

    # ------------------------------------------------------------------ 3. staged rows (chronological), 값_당분기 by the build_csm convention
    ext_rows = []
    for q in sorted(adopted):
        t = adopted[q]["chosen"]["items"]
        vals = {1: eok(t["open"]), 2: eok(t["new"]), 3: eok(t["fin"]), 4: eok(t["adj"]), 5: eok(t["amort"]), 6: eok(t["close"])}
        for no in range(1, 7):
            ext_rows.append({**meta, "항목번호": no, "항목명": CSM_ITEM_NM[no], "공시분기": q, "값": vals[no], "값_당분기": None})
    ytd = {no: {} for no in range(1, 7)}
    for (q, no), v in m_val.items():
        if q in YE_CTX:
            ytd[no][q] = v
    for r in core_staged + ext_rows:
        ytd[r["항목번호"]][r["공시분기"]] = r["값"]

    def derive(no, q, v):
        if no == BR.CSM_CLOSE:
            return v
        if no == BR.CSM_OPEN:
            p = BR._prev_q(q)
            return v if p is None else ytd[BR.CSM_CLOSE].get(p)
        return BR._flow_dangi(ytd[no], q)

    for r in ext_rows:
        d = derive(r["항목번호"], r["공시분기"], r["값"])
        r["값_당분기"] = round(d, 6) if isinstance(d, (int, float)) else d
    # quarter-only checks of the staged rows: new CSM >= 0, quarter identity
    qonly_rep, ok_q = {}, True
    for q in sorted(adopted):
        dd = {r["항목번호"]: r["값_당분기"] for r in ext_rows if r["공시분기"] == q}
        if dd[2] is not None:
            ident = dd[1] + dd[2] + dd[3] + dd[4] + dd[5] - dd[6]
            qonly_rep[q] = {"new_quarter_only": dd[2], "identity_residual": round(ident, 5)}
            ok_q &= dd[2] >= 0 and abs(ident) < 1e-4
        else:
            qonly_rep[q] = {"quarter_only": "not derivable (previous quarter not in the master set)", "close": dd[6]}
    rep["quarter_only"] = qonly_rep
    rep["checks"].append({"name": "quarter-only (당분기) 신계약 CSM >= 0 and quarter identity closes wherever derivable", "pass": ok_q})
    if not ok_q:
        raise SystemExit("quarter-only checks failed")

    # ------------------------------------------------------------------ 4. cross-check with the independent ILP master (2-4 보험부채 현황 CSM)
    ilp_rep, ok_ilp = {}, True
    for q in sorted(adopted):
        cl = adopted[q]["chosen"]["items"]["close"] / EOK
        v = ilp.get(q)
        if v is None:                                            # the ILP master carries items 10~15 only for 2023.1Q~3Q
            ilp_rep[q] = {"close_억원": round(cl, 2), "ilp_item3_억원": None, "match_to_rounding": "n/a (ILP master has no item 3 for this quarter)"}
            continue
        good = abs(round(cl) - v) <= 1
        ilp_rep[q] = {"close_억원": round(cl, 2), "ilp_item3_억원": v, "match_to_rounding": good}
        ok_ilp &= good
    # the held (old basis) quarters against the same master, to show what the ILP master carries for them
    for q, h in holds.items():
        cl = h["chosen"]["items"]["close"] / EOK
        ilp_rep[q] = {"close_억원": round(cl, 2), "ilp_item3_억원": ilp.get(q), "held": True,
                      "match_to_rounding": (abs(round(cl) - ilp[q]) <= 1) if ilp.get(q) is not None else "n/a (ILP master has no item 3 for this quarter)"}
    rep["ilp_crosscheck"] = ilp_rep
    rep["checks"].append({"name": "adopted close == insurance_liability_portfolio item 3 (일반모형 CSM), rounding", "pass": ok_ilp})
    if not ok_ilp:
        raise SystemExit("ILP cross-check failed: " + json.dumps(ilp_rep, ensure_ascii=False))

    # ------------------------------------------------------------------ 5. provenance cells
    side = []
    for q in sorted(adopted):
        a = adopted[q]
        pdf = latest_disclosure_pdfs(a["chosen"]["fy"], CODE)[0]
        cell = {"company_code": CODE, "quarter": q, "item_block": "csm_waterfall", "source_id": "DISCLOSURE",
                "source_file": str(pdf.relative_to(ROOT)).replace("\\", "/"), "as_of_date": a["spec"]["as_of"]}
        if a["conflict"]:
            cell["basis"] = "latest_filing_prior_column_restated"
        side.append(cell)

    # ------------------------------------------------------------------ 6. held rows (old basis; NOT loaded)
    held_rows = []
    for q in sorted(holds):
        t = holds[q]["chosen"]["items"]
        # old-basis print may carry a 기타(미결계정변동) row inside the CSM; it is folded into item 4 only here, where a plug-free close needs it
        adj = t["adj"] + t["other"]
        vals = {1: eok(t["open"]), 2: eok(t["new"]), 3: eok(t["fin"]), 4: eok(adj), 5: eok(t["amort"]), 6: eok(t["close"])}
        for no in range(1, 7):
            held_rows.append({**meta, "항목번호": no, "항목명": CSM_ITEM_NM[no], "공시분기": q, "값": vals[no], "값_당분기": None})
    hy = {no: {} for no in range(1, 7)}
    for r in held_rows:
        hy[r["항목번호"]][r["공시분기"]] = r["값"]
    for r in held_rows:
        no, q = r["항목번호"], r["공시분기"]
        if no == BR.CSM_CLOSE:
            d = r["값"]
        elif no == BR.CSM_OPEN:
            p = BR._prev_q(q)
            d = r["값"] if p is None else hy[BR.CSM_CLOSE].get(p)
        else:
            d = BR._flow_dangi(hy[no], q)
        r["값_당분기"] = round(d, 6) if isinstance(d, (int, float)) else d

    # ------------------------------------------------------------------ 7. amortisation schedules (staged only)
    am_rows, coarse_rows, am_rep = [], [], {}
    for q, (fy, pno) in AMORT_YEARLY.items():
        pdf, doc = docs.get(fy)
        pg = doc[pno - 1]
        if "기대상각기간별" not in R.norm(pg.get_text()):
            raise SystemExit(f"{q}: p{pno} is not the amortisation schedule")
        a = R.read_amort_page(pg)
        prob = R.check_amort(a)
        close = adopted[q]["chosen"]["items"]["close"]
        tot = a["total1"][7] if a["total1"] else None
        if prob or tot is None or abs(tot - close) > 2:
            raise SystemExit(f"{q} schedule: problems {prob} / 계 {tot} vs close {close}")
        yearly = a["total0"] + a["total1"][:2]
        am_rep[q] = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "page": pno, "format": "yearly 1..30+", "printed_total_계_천원": tot,
                     "closing_csm_천원": close, "total_minus_close_천원": tot - close, "buckets_1_to_10y_천원": yearly,
                     "tail_buckets_11_15_16_20_21_25_26_30_30plus_천원": a["total1"][2:7], "identity_problems": prob}
        for i, v in enumerate(yearly, 1):
            am_rows.append({**{k: meta[k] for k in ("원보험사코드", "원수사명", "티커", "생손보여부")}, "공시분기": q, "경과차년": i, "상각액": eok(v)})
    for q, (fy, pno) in AMORT_COARSE.items():
        pdf, doc = docs.get(fy)
        pg = doc[pno - 1]
        if "기대상각기간별" not in R.norm(pg.get_text()):
            raise SystemExit(f"{q}: p{pno} is not the amortisation schedule")
        c = R.read_coarse_schedule(pg)
        close = adopted[q]["chosen"]["items"]["close"]
        if not c["sum_ok"] or abs(c["total"] - close) > 2:
            raise SystemExit(f"{q} coarse schedule: {c} vs close {close}")
        am_rep[q] = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "page": pno, "format": "coarse 5 buckets (not representable in the 1~10 year schema)",
                     "buckets_천원": c["buckets"], "printed_total_천원": c["total"], "closing_csm_천원": close, "total_minus_close_천원": c["total"] - close}
        coarse_rows.append({**{k: meta[k] for k in ("원보험사코드", "원수사명", "티커", "생손보여부")}, "공시분기": q, "형식": "5구간(1년 이내 · 1~3년 · 3~5년 · 5~10년 · 10년 초과)",
                            "구간": COARSE_LABELS, "상각액_억원": [eok(v) for v in c["buckets"]], "합계_억원": eok(c["total"]),
                            "원천": {"pdf": am_rep[q]["pdf"], "page": pno}})
    for q, (fy, pno) in AMORT_OLD_BASIS.items():
        pdf, doc = docs.get(fy)
        am_rep[q] = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "page": pno, "format": "coarse, old (pre-restatement) basis",
                     "status": "HOLD: printed only on the old basis; the restated 2023 interim schedule is not printed in any later filing"}
    rep["amortisation"] = am_rep
    rep["checks"].append({"name": "amortisation schedules of the extension: identities, printed 계 == adopted closing CSM (+-2 천원)", "pass": True})

    # ------------------------------------------------------------------ 8. existing cells that become derivable (NOT written)
    derivable = []
    existing_dangi = dict(cur_dangi)                                 # (quarter, item) -> current 값_당분기 in the master
    for r in core_staged:
        existing_dangi[(r["공시분기"], r["항목번호"])] = r["값_당분기"]
    for (q, no), cur in sorted(existing_dangi.items()):
        if no == 6 or cur is not None:
            continue
        v = ytd[no].get(q)
        if v is None:
            continue
        d = derive(no, q, v)
        if d is not None:
            derivable.append({"공시분기": q, "항목번호": no, "현재_값_당분기": cur, "build_csm_규칙_도출값": round(d, 6)})
    rep["existing_cells_now_derivable_NOT_WRITTEN"] = derivable
    return {"report": rep, "wf_rows": ext_rows, "side": side, "am_rows": am_rows, "coarse_rows": coarse_rows, "held_rows": held_rows,
            "derivable_existing": derivable, "holds": holds, "adopted": {q: a["which"] for q, a in adopted.items()}}
