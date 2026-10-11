# -*- coding: utf-8 -*-
"""Lina Life (KR0074): quarterly CSM roll-forward + expected-amortisation schedule from the management-disclosure PDFs
(the reviewed interim notes attached to the 정기경영공시) -> staged master rows.  NO master is touched here;
load_lina_csm_backfill_20261011.py applies the staged rows (guarded, additive).

Ticket : inbox/parser/20261011T1700Z__orchestrator__MULTI_2023.1Q-2026.2Q__csm_backfill_annual_filers_from_disclosure.md
         (owner 2026-10-11: only Lina; six CSM waterfall items x 2026.2Q / 2026.1Q / 2025.3Q + the amortisation schedule)
Runlog : data/disclosure/_meta/csm_backfill_annual_filers_runlog_20261011.md
Output : data/_derived/csm_backfill_lina_20261011/{rows_waterfall,rows_amortization,sidecar_cells,build_report}.json

Source tables (fitz text layer, word coordinates, unit 천원 -> 억원 = /1e5, lossless):
  * "(5) ... 보험계약부채(자산)의 측정요소별 변동내역"  (PV | RA | CSM 공정가치법 | CSM 수정소급법 | CSM 전환이후 | 계)
      2026.2Q  FY2026_Q2 raw pdf  p91 (유배당) + p93 (유배당 외)   [<당반기>]
      2026.1Q  FY2026_Q1 raw pdf  p66 (유배당) + p68 (유배당 외)   [<당분기>]
      2025.3Q  FY2025_Q3 raw pdf  p63 (one table for the whole company)  [<당분기> = 9 months]
  * "(7) ... 기대상각기간별 보험계약마진 금액"  p96 / p71 / p66 (period-end), 합계 row
Mapping (same as the existing KR0074 year-end rows; proven below by reproducing the master's 2025.4Q and 2024.4Q/2023.4Q rows):
  1 기초 CSM = 기초 잔액 | 2 신계약 CSM = 최초 인식한 계약의 효과 | 3 이자 부리 = 보험금융손익
  4 가정 및 경험 조정 = 보험계약마진 조정하는 추정치의 변동분 | 5 CSM 상각 = 제공한 서비스 반영 인식한 보험계약마진 | 6 기말 CSM = 기말 잔액
  each = sum of the three CSM columns (공정가치법 + 수정소급법 + 전환이후), 유배당 + 유배당 외 summed in 천원 first.
Checks that ABORT the run when they fail (nothing is staged from a table that does not close):
  horizontal row identity + vertical roll-forward identity of EVERY column of EVERY page used; open+new+fin+adj+amort == close in
  천원 (no plug); 별도(회사) == 연결(연결실체) CSM numbers; amortisation schedule column/row/grand-total identities and 계 == closing CSM.

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_lina_csm_rows_20261011.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "data" / "_derived" / "csm_backfill_lina_20261011"
sys.path.insert(0, str(ROOT / "scripts"))
from _disclosure_pdf_paths import latest_disclosure_pdfs  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

CODE = "KR0074"
CORE_CTX = {"2023.4Q", "2024.4Q", "2025.4Q"}      # the year-end rows of Lina that the master held before the quarterly backfill
CSM_ITEM_NM = {1: "기초 CSM", 2: "신계약 CSM", 3: "이자 부리", 4: "가정 및 경험 조정", 5: "CSM 상각", 6: "기말 CSM"}
EOK = 100_000                       # 1억원 = 100,000 천원

# quarter -> source pages (1-based). cur = this quarter's table(s), prior = comparative (same filing), con = 연결 copies
PLAN = {
    "2026.2Q": {"fy": "FY2026_Q2", "as_of": "2026-06-30", "prior_q": "2025.2Q",
                "cur": {"유배당": 91, "유배당 외": 93}, "prior": {"유배당": 92, "유배당 외": 94},
                "con_cur": {"유배당": 161, "유배당 외": 163}, "con_prior": {"유배당": 162, "유배당 외": 164},
                "amort": 96, "amort_prior_year_end": 97, "amort_con": 166},
    "2026.1Q": {"fy": "FY2026_Q1", "as_of": "2026-03-31", "prior_q": "2025.1Q",
                "cur": {"유배당": 66, "유배당 외": 68}, "prior": {"유배당": 67, "유배당 외": 69},
                "con_cur": {"유배당": 137, "유배당 외": 139}, "con_prior": {"유배당": 138, "유배당 외": 140},
                "amort": 71, "amort_prior_year_end": 72, "amort_con": 142},
    "2025.3Q": {"fy": "FY2025_Q3", "as_of": "2025-09-30", "prior_q": "2024.3Q",
                "cur": {"전사": 63}, "prior": {"전사": 64},
                "con_cur": {"전사": 130}, "con_prior": {"전사": 131},
                "amort": 66, "amort_prior_year_end": 67, "amort_con": 133},
}
# regression: the same reader must reproduce the EXISTING year-end rows of the master (same column definitions)
REGRESSION = {
    "2025.4Q": {"fy": "FY2025_Q4", "pages": {"유배당": 232, "유배당 외": 234}},
    "2024.4Q": {"fy": "FY2024_Q4", "pages": {"전사": 212}},
    "2023.4Q": {"fy": "FY2024_Q4", "pages": {"전사": 213}, "note": "FY2024 filing <전기> column (restated basis, = gold overlay)"},
}
# comparative (전기) columns of the 2025.4Q filing = FY2024 -> must equal master 2024.4Q too
REGRESSION_PRIOR = {"2024.4Q": {"fy": "FY2025_Q4", "pages": {"유배당": 233, "유배당 외": 235}}}

# ----------------------------------------------------------------------------------------------- table reader
NUM_RE = re.compile(r"^\(?-?[\d,]+(?:\.\d+)?\)?$")
DASHES = {"-", "\u2013", "\u2014", "\u2212"}
LABELS = {
    "open": "기초잔액", "fut": "미래서비스관련변동", "adj": "보험계약마진조정하는추정치의변동분",
    "onerous": "손실부담계약집합의손실(환입)", "new": "최초인식한계약의효과", "cur": "현행서비스관련변동",
    "amort": "제공한서비스반영인식한보험계약마진", "rarel": "위험해제에대한위험조정의변동분", "exp": "경험조정",
    "inc": "발생사고부채이행현금흐름변동", "cf": "현금흐름", "cf_prem": "수취한보험료", "cf_acq": "보험취득현금흐름",
    "cf_claims": "발생한보험금과기타보험서비스비용", "fin": "보험금융손익", "fin_pl": "당기손익인식",
    "fin_oci": "기타포괄손익인식", "close": "기말잔액",
}
CSM_COLS = (2, 3, 4)


def norm(s: str) -> str:
    return re.sub(r"[\s\u3000]+", "", s)


def is_num_token(t: str) -> bool:
    t = t.strip()
    return t in DASHES or (bool(NUM_RE.match(t)) and any(ch.isdigit() for ch in t))


def to_int(t: str) -> int:
    t = t.strip()
    if t in DASHES:
        return 0
    neg = t.startswith("(") and t.endswith(")")
    core = t.strip("()").replace(",", "")
    if "." in core:
        raise ValueError(f"decimal in a 천원 table: {t!r}")
    return -int(core) if neg else int(core)


def page_rows(page, ytol: float = 2.6):
    words = page.get_text("words")
    items = sorted(((0.5 * (w[1] + w[3]), w[0], w[2], w[4]) for w in words), key=lambda a: (a[0], a[1]))
    rows, cur, cur_y = [], [], None
    for yc, x0, x1, t in items:
        if cur_y is None or abs(yc - cur_y) <= ytol:
            cur.append((x0, x1, t))
            cur_y = yc if cur_y is None else (cur_y * (len(cur) - 1) + yc) / len(cur)
        else:
            rows.append(sorted(cur))
            cur, cur_y = [(x0, x1, t)], yc
    if cur:
        rows.append(sorted(cur))
    return rows


def split_row(row):
    label_parts, nums, seen = [], [], False
    for _x0, _x1, t in row:
        if is_num_token(t):
            seen = True
            nums.append(t)
        elif not seen:
            label_parts.append(t)
        else:
            label_parts.append("\u0001" + t)
    return norm("".join(label_parts)), nums


def read_rollforward(page) -> dict:
    got, dup, bad = {}, [], []
    for r in page_rows(page):
        lab, nums = split_row(r)
        if not nums:
            continue
        for key, want in LABELS.items():
            if lab == want:
                if len(nums) != 6:
                    bad.append((key, lab, nums))
                    continue
                if key in got:
                    dup.append(key)
                else:
                    got[key] = [to_int(t) for t in nums]
    return {"rows": got, "dup": dup, "bad": bad}


def check_rollforward(rows: dict) -> list:
    prob = []
    for k in ("open", "fut", "adj", "new", "cur", "amort", "inc", "cf", "fin", "close", "onerous", "rarel", "exp", "fin_pl", "fin_oci"):
        if k not in rows:
            prob.append(f"missing row {k}")
    if prob:
        return prob
    for k, v in rows.items():                                   # horizontal: 5 components = total column
        if sum(v[:5]) != v[5]:
            prob.append(f"row {k}: components {sum(v[:5])} != total {v[5]}")
    for j in range(6):                                          # vertical roll-forward, every column
        s = sum(rows[k][j] for k in ("open", "fut", "cur", "inc", "cf", "fin"))
        if s != rows["close"][j]:
            prob.append(f"column {j}: roll-forward {s} != close {rows['close'][j]}")
        if rows["adj"][j] + rows["onerous"][j] + rows["new"][j] != rows["fut"][j]:
            prob.append(f"column {j}: 미래서비스 sub-rows")
        if rows["amort"][j] + rows["rarel"][j] + rows["exp"][j] != rows["cur"][j]:
            prob.append(f"column {j}: 현행서비스 sub-rows")
        if rows["fin_pl"][j] + rows["fin_oci"][j] != rows["fin"][j]:
            prob.append(f"column {j}: 보험금융손익 sub-rows")
    return prob


def csm_items(rows: dict) -> dict:
    s = lambda k: sum(rows[k][j] for j in CSM_COLS)             # noqa: E731
    return {"open": s("open"), "new": s("new"), "fin": s("fin"), "adj": s("adj"), "amort": s("amort"), "close": s("close")}


def read_amort_page(page) -> dict:
    halves, totals, other, half = [[], []], [None, None], [], 0
    for r in page_rows(page):
        lab, nums = split_row(r)
        if not nums:
            continue
        if len(nums) != 8:
            other.append((lab, nums))
            continue
        vals = [to_int(t) for t in nums]
        if lab.endswith("합계"):
            totals[half] = vals
            half = min(half + 1, 1)
            if totals[1] is not None:
                break
        else:
            halves[half].append((lab, vals))
    return {"half0": halves[0], "half1": halves[1], "total0": totals[0], "total1": totals[1]}


def check_amort(a: dict) -> list:
    prob = []
    if a["total0"] is None or a["total1"] is None:
        return ["missing 합계 row(s)"]
    for h, key in ((0, "half0"), (1, "half1")):
        tot = a["total0"] if h == 0 else a["total1"]
        for j in range(8):
            s = sum(v[j] for _, v in a[key])
            if s != tot[j]:
                prob.append(f"half{h} col {j}: portfolio sum {s} != 합계 {tot[j]}")
    if sum(a["total0"]) + sum(a["total1"][:7]) != a["total1"][7]:
        prob.append("15 buckets do not add up to the printed 계")
    if len(a["half0"]) != len(a["half1"]):
        prob.append("half row counts differ")
    else:
        for (l0, v0), (_l1, v1) in zip(a["half0"], a["half1"]):
            if sum(v0) + sum(v1[:7]) != v1[7]:
                prob.append(f"row {l0}: 15-bucket sum != 계")
    return prob


# ----------------------------------------------------------------------------------------------- helpers
def open_pdf(fy: str):
    pdf = latest_disclosure_pdfs(fy, CODE)[0]               # the repo's single interpreter of raw/ vs pdf/ (tests/test_disclosure_raw_pdf_wiring.py)
    return pdf, fitz.open(pdf)


def read_pages(doc, pages: dict, what: str) -> dict:
    """{account: page} -> {account: {rows, items, page}}; aborts if a page does not close."""
    out = {}
    for acct, p in pages.items():
        rf = read_rollforward(doc[p - 1])
        if rf["bad"] or rf["dup"]:
            raise SystemExit(f"{what} p{p}: unreadable rows bad={rf['bad']} dup={rf['dup']}")
        prob = check_rollforward(rf["rows"])
        if prob:
            raise SystemExit(f"{what} p{p} ({acct}): identity problems {prob}")
        out[acct] = {"page": p, "rows": rf["rows"], "items": csm_items(rf["rows"])}
    return out


def sum_items(parts: dict) -> dict:
    keys = ("open", "new", "fin", "adj", "amort", "close")
    return {k: sum(v["items"][k] for v in parts.values()) for k in keys}


def eok(x: int) -> float:
    return round(x / EOK, 5)


def r1(x: int) -> float:
    return round(x / EOK + 1e-12, 1)


def main() -> int:
    import build_root_masters as BR                               # only for the 당분기 helpers (no side effect at import)

    wf_master = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
    am_master = json.loads((ROOT / "CSM_amortization.json").read_text(encoding="utf-8"))
    meta = next({k: r[k] for k in ("원보험사코드", "원수사명", "티커", "생손보여부")} for r in wf_master if r["원보험사코드"] == CODE)
    m_val = {(r["공시분기"], r["항목번호"]): r["값"] for r in wf_master if r["원보험사코드"] == CODE}
    report = {"ticket": "20261011T1700Z csm_backfill_annual_filers (Lina only)", "quarters": {}, "regression": {}, "checks": []}

    # ---------------------------------------------------------------- 0. regression against the existing year-end rows
    item_no = {"open": 1, "new": 2, "fin": 3, "adj": 4, "amort": 5, "close": 6}
    reg_ok = True
    reg_tot = {}                                                   # exact 천원 totals read from the year-end filings
    for q, spec in REGRESSION.items():
        pdf, doc = open_pdf(spec["fy"])
        parts = read_pages(doc, spec["pages"], f"regression {q}")
        tot = sum_items(parts)
        reg_tot[q] = tot
        rows = {}
        for k, no in item_no.items():
            master = m_val[(q, no)]
            got = r1(tot[k])
            rows[k] = {"pdf_천원": tot[k], "pdf_억원_1dp": got, "master": master, "equal_at_1dp": abs(got - master) < 0.0501}
        reg_ok &= all(v["equal_at_1dp"] for v in rows.values())
        report["regression"][q] = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
                                   "pages": spec["pages"], "rows": rows, "note": spec.get("note")}
    for q, spec in REGRESSION_PRIOR.items():                       # 2024.4Q again, from the comparative columns of the FY2025 filing
        pdf, doc = open_pdf(spec["fy"])
        parts = read_pages(doc, spec["pages"], f"regression-prior {q}")
        tot = sum_items(parts)
        rows = {k: {"pdf_천원": tot[k], "pdf_억원_1dp": r1(tot[k]), "master": m_val[(q, no)],
                    "equal_at_1dp": abs(r1(tot[k]) - m_val[(q, no)]) < 0.0501} for k, no in item_no.items()}
        reg_ok &= all(v["equal_at_1dp"] for v in rows.values())
        report["regression"][q + " (from FY2025_Q4 <전기>)"] = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
                                                                 "pages": spec["pages"], "rows": rows}
    report["checks"].append({"name": "regression: reader reproduces the existing KR0074 year-end master rows (6 items, 1dp)", "pass": reg_ok})
    if not reg_ok:
        (STAGE / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        raise SystemExit("regression against the existing master rows FAILED -- column definition differs, nothing staged")

    # ---------------------------------------------------------------- 1. target quarters
    ytd_ref = {}                                                   # quarter -> 6 items in 천원 (target quarters)
    for q, spec in PLAN.items():
        pdf, doc = open_pdf(spec["fy"])
        cur = read_pages(doc, spec["cur"], f"{q} 별도")
        con = read_pages(doc, spec["con_cur"], f"{q} 연결")
        pri = read_pages(doc, spec["prior"], f"{q} 전기비교")
        t, tc, tp = sum_items(cur), sum_items(con), sum_items(pri)
        same_sep_con = (t == tc)
        resid = t["open"] + t["new"] + t["fin"] + t["adj"] + t["amort"] - t["close"]
        ytd_ref[q] = t
        report["quarters"][q] = {
            "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "pages_separate": spec["cur"], "pages_consolidated": spec["con_cur"],
            "pages_prior_comparative": spec["prior"], "per_account_천원": {a: v["items"] for a, v in cur.items()},
            "sum_천원": t, "identity_residual_천원": resid, "separate_equals_consolidated": same_sep_con,
            "comparative_prior_period": spec["prior_q"], "comparative_sum_천원": tp,
        }
        if resid != 0:
            raise SystemExit(f"{q}: open+new+fin+adj+amort != close (residual {resid} 천원) -- would need a plug, refusing")
        if not same_sep_con:
            raise SystemExit(f"{q}: 별도 != 연결 CSM numbers {t} vs {tc}")
        report["checks"].append({"name": f"{q} identity (천원, no plug) + separate==consolidated", "pass": True})

    # ---------------------------------------------------------------- 2. YTD chain checks (flows monotone) incl. comparatives
    chain = {"2025.1Q": report["quarters"]["2026.1Q"]["comparative_sum_천원"],
             "2025.2Q": report["quarters"]["2026.2Q"]["comparative_sum_천원"],
             "2025.3Q": ytd_ref["2025.3Q"],
             "2025.4Q": reg_tot["2025.4Q"]}                         # exact 천원 of the 2025.4Q filing (== master at 1dp, proven above)
    mono = {}
    for k, sign in (("new", 1), ("fin", 1), ("amort", -1)):
        seq = [sign * chain[q][k] for q in ("2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q")]
        mono[k] = {"seq_억원": [round(sign * v / EOK, 1) for v in seq], "monotone": all(b >= a for a, b in zip(seq, seq[1:]))}
    seq26 = {k: [sign * ytd_ref[q][k] for q in ("2026.1Q", "2026.2Q")] for k, sign in (("new", 1), ("fin", 1), ("amort", -1))}
    mono26 = {k: {"seq_억원": [round(v / EOK, 1) for v in s], "monotone": s[1] >= s[0]} for k, s in seq26.items()}
    report["ytd_monotonicity_2025"] = mono
    report["ytd_monotonicity_2026"] = mono26
    mono_ok = all(v["monotone"] for v in mono.values()) and all(v["monotone"] for v in mono26.values())
    report["checks"].append({"name": "YTD monotone (신계약, 이자, 상각 magnitude) 2025.1Q<=2Q<=3Q<=4Q and 2026.1Q<=2Q", "pass": mono_ok})
    if not mono_ok:
        raise SystemExit("YTD monotonicity failed")

    # ---------------------------------------------------------------- 3. continuity (opening vs previous close in the master)
    cont = {}
    for q in PLAN:
        y = int(q[:4])
        prev_close = m_val.get((f"{y - 1}.4Q", 6))
        o = ytd_ref[q]["open"] / EOK
        cont[q] = {"opening_억원": round(o, 5), "master_prev_year_end_close": prev_close,
                   "delta_억원": round(o - prev_close, 5), "equal_at_1dp": abs(round(o, 1) - prev_close) < 1e-9}
    report["continuity_opening_vs_master_prev_year_end"] = cont
    report["checks"].append({"name": "opening == master previous year-end close (1dp)", "pass": all(v["equal_at_1dp"] for v in cont.values())})
    if not all(v["equal_at_1dp"] for v in cont.values()):
        raise SystemExit("opening != previous year-end close in the master")
    # 2025.3Q close -> 2025.4Q close through the derived Q4-only flows (exact), and 2026.1Q -> 2026.2Q
    q4 = {k: chain["2025.4Q"][k] - chain["2025.3Q"][k] for k in ("new", "fin", "adj", "amort")}
    q4_close = ytd_ref["2025.3Q"]["close"] + sum(q4.values())
    report["sequential_2025.3Q_to_4Q"] = {"q4_only_flows_억원": {k: round(v / EOK, 4) for k, v in q4.items()},
                                          "3Q_close+q4_flows_억원": round(q4_close / EOK, 4),
                                          "master_2025.4Q_close": m_val[("2025.4Q", 6)],
                                          "delta_억원": round(q4_close / EOK - m_val[("2025.4Q", 6)], 4)}
    # the two filings print the 2025 opening as 2,764,859,849 (one table) and 2,764,859,850 (two accounts summed): +-1 천원 rounding
    seq_ok = abs(q4_close - reg_tot["2025.4Q"]["close"]) <= 2 and abs(q4_close / EOK - m_val[("2025.4Q", 6)]) < 0.1
    report["checks"].append({"name": "2025.3Q close + derived Q4-only flows == 2025.4Q close (+-2 천원; master 1dp within 0.1)", "pass": seq_ok})
    if not seq_ok:
        raise SystemExit("2025.3Q -> 2025.4Q sequential closure failed")

    # ---------------------------------------------------------------- 4. staged waterfall rows (+ 값_당분기 by the build_csm convention)
    staged, rows_by_q = [], {}
    for q in ("2025.3Q", "2026.1Q", "2026.2Q"):
        t = ytd_ref[q]
        vals = {1: eok(t["open"]), 2: eok(t["new"]), 3: eok(t["fin"]), 4: eok(t["adj"]), 5: eok(t["amort"]), 6: eok(t["close"])}
        rows_by_q[q] = vals
        for no in range(1, 7):
            staged.append({**meta, "항목번호": no, "항목명": CSM_ITEM_NM[no], "공시분기": q, "값": vals[no], "값_당분기": None})
    # derive 값_당분기 exactly like build_root_masters.build_csm() on (existing KR0074 rows + staged rows).  The context is FROZEN to the
    # year-end rows the master held when these three quarters were loaded: quarterly rows loaded later (extension) must not change the
    # staged values of rows that are already in the master (the loader would see a collision).
    ytd = {no: {q: m_val[(q, no)] for (q, n) in m_val if n == no and q in CORE_CTX} for no in range(1, 7)}
    for r in staged:
        ytd[r["항목번호"]][r["공시분기"]] = r["값"]
    for r in staged:
        no, q, v = r["항목번호"], r["공시분기"], r["값"]
        if no == BR.CSM_CLOSE:
            d = v
        elif no == BR.CSM_OPEN:
            p = BR._prev_q(q)
            d = v if p is None else ytd[BR.CSM_CLOSE].get(p)
        else:
            d = BR._flow_dangi(ytd[no], q)
        r["값_당분기"] = round(d, 6) if isinstance(d, (int, float)) else d
    # what build_csm() WOULD now put into the existing 2025.4Q rows (not written -- existing cells stay as they are)
    pending_2025_4q = {}
    for no in range(1, 7):
        if no == BR.CSM_CLOSE:
            d = m_val[("2025.4Q", 6)]
        elif no == BR.CSM_OPEN:
            d = ytd[BR.CSM_CLOSE].get("2025.3Q")
        else:
            d = BR._flow_dangi(ytd[no], "2025.4Q")
        pending_2025_4q[no] = None if d is None else round(d, 6)
    report["pending_derived_2025.4Q_값_당분기_NOT_WRITTEN"] = pending_2025_4q
    # quarter-only identity of the staged 2026.2Q row (open of the quarter = 2026.1Q close)
    d26 = {r["항목번호"]: r["값_당분기"] for r in staged if r["공시분기"] == "2026.2Q"}
    qid = d26[1] + d26[2] + d26[3] + d26[4] + d26[5] - d26[6]
    report["quarter_only_identity_2026.2Q_억원"] = round(qid, 6)
    report["checks"].append({"name": "2026.2Q quarter-only (당분기) waterfall closes", "pass": abs(qid) < 1e-4})
    report["staged_waterfall_억원"] = {q: v for q, v in rows_by_q.items()}
    report["staged_값_당분기"] = {q: {r["항목번호"]: r["값_당분기"] for r in staged if r["공시분기"] == q} for q in rows_by_q}

    # ---------------------------------------------------------------- 5. amortisation schedules
    am_rows, am_prov = [], {}
    for q, spec in PLAN.items():
        pdf, doc = open_pdf(spec["fy"])
        pg = doc[spec["amort"] - 1]
        txt = norm(pg.get_text())
        if "발행한보험계약의기대상각기간별" not in txt:
            raise SystemExit(f"{q} p{spec['amort']}: not the issued-contracts schedule")
        a = read_amort_page(pg)
        prob = check_amort(a)
        con = read_amort_page(doc[spec["amort_con"] - 1])
        if prob or check_amort(con):
            raise SystemExit(f"{q} amortisation schedule identity problems {prob} / {check_amort(con)}")
        if (a["total0"], a["total1"]) != (con["total0"], con["total1"]):
            raise SystemExit(f"{q}: schedule 별도 != 연결")
        close = ytd_ref[q]["close"]
        tot = a["total1"][7]
        yearly = a["total0"] + a["total1"][:2]                      # 1..10 years
        tail = a["total1"][2:7]                                      # 11~15, 16~20, 21~25, 26~30, 30+
        am_prov[q] = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "page": spec["amort"], "page_consolidated": spec["amort_con"],
                      "unit": "천원", "printed_total_계_천원": tot, "closing_csm_천원": close, "total_minus_close_천원": tot - close,
                      "buckets_1_to_10y_천원": yearly, "tail_buckets_11_15_16_20_21_25_26_30_30plus_천원": tail,
                      "tail_억원": [eok(v) for v in tail], "identity_problems": prob}
        if abs(tot - close) > 2:
            raise SystemExit(f"{q}: schedule 계 {tot} != closing CSM {close} (천원)")
        for i, v in enumerate(yearly, 1):
            am_rows.append({**{k: meta[k] for k in ("원보험사코드", "원수사명", "티커", "생손보여부")}, "공시분기": q, "경과차년": i, "상각액": eok(v)})
    am_rows.sort(key=lambda r: (r["공시분기"], r["경과차년"]))           # chronological, like every other block of the master
    report["amortisation"] = am_prov
    report["checks"].append({"name": "amortisation schedules: identities, 별도==연결, printed 계 == closing CSM (|d|<=2 천원)", "pass": True})
    # the existing 2025.4Q master rows vs the two schedules in the FY2025_Q4 filing
    pdf4, doc4 = open_pdf("FY2025_Q4")
    s_cur, s_prv = read_amort_page(doc4[245 - 1]), read_amort_page(doc4[246 - 1])
    m_am = {r["경과차년"]: r["상각액"] for r in am_master if r["원보험사코드"] == CODE and r["공시분기"] == "2025.4Q"}
    cur8 = [round((s_cur["total0"] + s_cur["total1"][:2])[i] / EOK, 1) for i in range(8)]
    prv8 = [round((s_prv["total0"] + s_prv["total1"][:2])[i] / EOK, 1) for i in range(8)]
    report["existing_master_amortisation_2025.4Q"] = {
        "master_rows_1_to_10": [m_am.get(i) for i in range(1, 11)],
        "pdf_2025-12-31_schedule_(당기말)_1_to_8": cur8, "pdf_2024-12-31_schedule_(전기말)_1_to_8": prv8,
        "master_equals_2025-12-31": [m_am.get(i + 1) for i in range(8)] == cur8,
        "master_equals_2024-12-31": [m_am.get(i + 1) for i in range(8)] == prv8,
        "pdf_page_당기말": 245, "pdf_page_전기말": 246,
        "correct_2025-12-31_1_to_10_억원": [eok(v) for v in (s_cur["total0"] + s_cur["total1"][:2])],
    }

    # ---------------------------------------------------------------- 6. provenance cells
    side = []
    for q, spec in PLAN.items():
        pdf = latest_disclosure_pdfs(spec["fy"], CODE)[0]
        side.append({"company_code": CODE, "quarter": q, "item_block": "csm_waterfall", "source_id": "DISCLOSURE",
                     "source_file": str(pdf.relative_to(ROOT)).replace("\\", "/"), "as_of_date": spec["as_of"]})
    side.sort(key=lambda c: c["quarter"])

    # ---------------------------------------------------------------- 7. extension: the remaining eight quarters (2023.1Q .. 2025.2Q)
    import _lina_csm_ext_20261011 as EXT
    cur_dangi = {(r["공시분기"], r["항목번호"]): r["값_당분기"] for r in wf_master if r["원보험사코드"] == CODE}
    ext = EXT.run(meta=meta, m_val=m_val, cur_dangi=cur_dangi, reg_tot=reg_tot, ytd_core=ytd_ref, core_staged=staged, BR=BR)
    report["ext"] = ext["report"]
    for c in ext["report"]["checks"]:
        report["checks"].append(c)
    core_n, core_am_n, core_side_n = len(staged), len(am_rows), len(side)
    staged_all = staged + ext["wf_rows"]                              # core rows first and unchanged, then the new quarters chronologically
    am_all = sorted(am_rows + ext["am_rows"], key=lambda r: (r["공시분기"], r["경과차년"]))
    side_all = sorted(side + ext["side"], key=lambda c: c["quarter"])

    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / "rows_waterfall.json").write_text(json.dumps(staged_all, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    (STAGE / "rows_amortization.json").write_text(json.dumps(am_all, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    (STAGE / "sidecar_cells.json").write_text(json.dumps(side_all, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    (STAGE / "rows_amortization_coarse.json").write_text(json.dumps(ext["coarse_rows"], ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    held_doc = {"_what": ("라이나 2023.1Q·2023.2Q CSM 워터폴: 옛(재작성 전) 기준으로만 인쇄돼 있어 적재하지 않고 보류한 행. 기초 22,082.5억 ≠ 마스터 2023.4Q 기초 35,264.0억(재작성)이라 "
                          "같은 회계연도 기초 불일치(WITHIN_FY_OPENING_DRIFT)가 되고 한 계열에 두 기준이 섞인다. owner 가 옛 기준 적재 + 예외 등재를 정하면 그대로 적재 가능한 행."),
                "holds": {q: {"reason": h["reason"], "adopted_print": h["which"], "pages": h["chosen"]["pages"], "pdf": h["chosen"]["pdf"]} for q, h in ext["holds"].items()},
                "rows": ext["held_rows"]}
    (STAGE / "held_rows_waterfall.json").write_text(json.dumps(held_doc, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    (STAGE / "proposed_derived_dangi_existing.json").write_text(
        json.dumps({"_what": ("이번 확장으로 직전 분기가 마스터에 생겨 build_csm() 규칙대로 값_당분기가 도출 가능해진 기존 칸(현재 None). 기존 칸 변경 0 원칙이라 쓰지 않았다. "
                              "승인 시 값_당분기 None → 도출값만 셀 단위 + 옛 값 guard 로 갱신."), "cells": ext["derivable_existing"]},
                   ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    (STAGE / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"staged: waterfall {len(staged_all)} rows ({len({r['공시분기'] for r in staged_all})} quarters; core {core_n} + extension {len(ext['wf_rows'])}) | "
          f"amortisation {len(am_all)} rows (core {core_am_n} + extension {len(ext['am_rows'])}; coarse staged separately {len(ext['coarse_rows'])}) | "
          f"sidecar {len(side_all)} cells (core {core_side_n} + extension {len(ext['side'])}) | held {len(ext['held_rows'])} rows | "
          f"existing cells now derivable {len(ext['derivable_existing'])}")
    for h in ext["holds"].values():
        print("HOLD", h["q"], "-", h["reason"])
    for c in report["checks"]:
        print(("PASS " if c["pass"] else "FAIL ") + c["name"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
