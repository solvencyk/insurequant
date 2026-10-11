# -*- coding: utf-8 -*-
"""Table reader for the Lina Life (KR0074) management-disclosure PDFs (fitz text layer, word coordinates).

Written independently of the survey code under data/_derived/csm_backfill_survey_20261011 (own row clustering, own checks).

Two table families are read:
  * the CSM roll-forward note  "(5) ... 보험계약부채(자산)의 측정요소별 변동내역 (단위: 천원)"
        columns: 미래현금흐름 현재가치 | 위험조정 | CSM 공정가치법 | CSM 수정소급법 | CSM 전환이후 | 보험계약부채(자산)  (6 numbers per row)
  * the expected-amortisation schedule "(7) ... 기대상각기간별 보험계약마진 금액 (단위: 천원)"
        (two stacked half-tables: 1년..8년 and 9년,10년,11~15년,16~20년,21~25년,26~30년,30년 이후,계)

Every number that is used is protected by two independent identities (see check_rollforward):
  * horizontal: the five component columns of a row add up to the 6th (total) column
  * vertical  : 기초 + 미래서비스 + 현행서비스 + 발생사고부채 + 현금흐름 + 보험금융손익 = 기말 for each of the 6 columns
"""
from __future__ import annotations

import re
from typing import Iterable

NUM_RE = re.compile(r"^\(?-?[\d,]+(?:\.\d+)?\)?$")
DASHES = {"-", "–", "—", "−"}


def norm(s: str) -> str:
    return re.sub(r"[\s　]+", "", s)


def is_num_token(t: str) -> bool:
    t = t.strip()
    if t in DASHES:
        return True
    return bool(NUM_RE.match(t)) and any(ch.isdigit() for ch in t)


def to_int(t: str) -> int:
    t = t.strip()
    if t in DASHES:
        return 0
    neg = t.startswith("(") and t.endswith(")")
    core = t.strip("()").replace(",", "")
    if "." in core:
        raise ValueError(f"decimal in 천원 table: {t!r}")
    v = int(core)
    return -v if neg else v


def page_rows(page, ytol: float = 2.6):
    """-> list of rows, each a list of (x0, x1, text) sorted by x; rows sorted by y (top to bottom)."""
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
    """-> (label_norm, [number tokens as int]) -- label = non-numeric tokens left of the first numeric token."""
    label_parts, nums = [], []
    seen_num = False
    for x0, x1, t in row:
        if is_num_token(t):
            seen_num = True
            nums.append(t)
        elif not seen_num:
            label_parts.append(t)
        else:
            # text after numbers (footnote glued to a row) -- keep out of label, flag
            label_parts.append("\u0001" + t)
    return norm("".join(label_parts)), nums


# --------------------------------------------------------------------------- roll-forward
LABELS = {
    "open": "기초잔액",
    "fut": "미래서비스관련변동",
    "adj": "보험계약마진조정하는추정치의변동분",
    "onerous": "손실부담계약집합의손실(환입)",
    "new": "최초인식한계약의효과",
    "cur": "현행서비스관련변동",
    "amort": "제공한서비스반영인식한보험계약마진",
    "rarel": "위험해제에대한위험조정의변동분",
    "exp": "경험조정",
    "inc": "발생사고부채이행현금흐름변동",
    "cf": "현금흐름",
    "cf_prem": "수취한보험료",
    "cf_acq": "보험취득현금흐름",
    "cf_claims": "발생한보험금과기타보험서비스비용",
    "fin": "보험금융손익",
    "fin_pl": "당기손익인식",
    "fin_oci": "기타포괄손익인식",
    "close": "기말잔액",
}


def read_rollforward(page):
    """Read one measurement-component roll-forward page -> dict(label_key -> [6 ints]) + diagnostics.

    The first row whose normalised label equals the key label wins; a second occurrence is reported (the 보험계약자산/부채
    sub-rows under 기초/기말 have different labels, so duplicates would indicate two tables on one page)."""
    rows = page_rows(page)
    got, dup, bad = {}, [], []
    for r in rows:
        lab, nums = split_row(r)
        if not nums:
            continue
        for key, want in LABELS.items():
            if lab == want:
                if len(nums) != 6:
                    bad.append((key, lab, nums))
                    continue
                vals = [to_int(t) for t in nums]
                if key in got:
                    dup.append(key)
                else:
                    got[key] = vals
    return {"rows": got, "duplicates": dup, "bad": bad}


def check_rollforward(rows: dict):
    """-> list of problems (empty = clean).  rows: label_key -> [PV, RA, CSM_FVA, CSM_MRA, CSM_POST, TOTAL] (천원)."""
    prob = []
    need = ["open", "fut", "adj", "new", "cur", "amort", "inc", "cf", "fin", "close"]
    for k in need:
        if k not in rows:
            prob.append(f"missing row {k}")
    if prob:
        return prob
    # horizontal: columns 0..4 sum to column 5
    for k, v in rows.items():
        if sum(v[:5]) != v[5]:
            prob.append(f"row {k}: components {sum(v[:5])} != total {v[5]}")
    # vertical roll-forward per column
    for j in range(6):
        s = sum(rows[k][j] for k in ("open", "fut", "cur", "inc", "cf", "fin"))
        if s != rows["close"][j]:
            prob.append(f"column {j}: open+fut+cur+inc+cf+fin = {s} != close {rows['close'][j]}")
    # sub-row identities (only if the sub rows were read)
    if "onerous" in rows:
        for j in range(6):
            if rows["adj"][j] + rows["onerous"][j] + rows["new"][j] != rows["fut"][j]:
                prob.append(f"fut sub-rows column {j}: {rows['adj'][j] + rows['onerous'][j] + rows['new'][j]} != {rows['fut'][j]}")
    if "rarel" in rows and "exp" in rows:
        for j in range(6):
            if rows["amort"][j] + rows["rarel"][j] + rows["exp"][j] != rows["cur"][j]:
                prob.append(f"cur sub-rows column {j}: {rows['amort'][j] + rows['rarel'][j] + rows['exp'][j]} != {rows['cur'][j]}")
    if "fin_pl" in rows and "fin_oci" in rows:
        for j in range(6):
            if rows["fin_pl"][j] + rows["fin_oci"][j] != rows["fin"][j]:
                prob.append(f"fin sub-rows column {j}: {rows['fin_pl'][j] + rows['fin_oci'][j]} != {rows['fin'][j]}")
    return prob


CSM_COLS = (2, 3, 4)


def csm_items(rows: dict) -> dict:
    """CSM (sum of the three CSM columns) of the six master items, in 천원."""
    s = lambda k: sum(rows[k][j] for j in CSM_COLS)
    return {"open": s("open"), "new": s("new"), "fin": s("fin"), "adj": s("adj"), "amort": s("amort"), "close": s("close"),
            "total_col": {k: rows[k][5] for k in ("open", "close")}}


# --------------------------------------------------------------------------- amortisation schedule
def read_amort_page(page):
    """Read the expected-CSM-amortisation schedule of one page (two stacked half-tables, 8 numbers per row).

    Rows with exactly 8 numeric tokens are collected in page order; the first '합계' row closes half 0 (1년..8년), the
    second closes half 1 (9년, 10년, 11~15년, 16~20년, 21~25년, 26~30년, 30년 이후, 계).
    -> dict(half0=[rows], half1=[rows], total0=[8], total1=[8], other=[unreadable rows])  (rows = (label, [8 ints]))"""
    rows = page_rows(page)
    halves = [[], []]
    totals = [None, None]
    other = []
    half = 0
    for r in rows:
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
    return {"half0": halves[0], "half1": halves[1], "total0": totals[0], "total1": totals[1], "other": other}


def check_amort(a: dict):
    """-> problems.  Column sums of the portfolio rows == 합계 per half; first-half sum + second-half first 7 == printed 계."""
    prob = []
    if a["total0"] is None or a["total1"] is None:
        return ["missing 합계 row(s)"]
    for h, key in ((0, "half0"), (1, "half1")):
        tot = a["total0"] if h == 0 else a["total1"]
        for j in range(8):
            s = sum(v[j] for _, v in a[key])
            if s != tot[j]:
                prob.append(f"half{h} col {j}: portfolio sum {s} != 합계 {tot[j]}")
    grand = sum(a["total0"]) + sum(a["total1"][:7])
    if grand != a["total1"][7]:
        prob.append(f"sum of 15 buckets {grand} != printed 계 {a['total1'][7]}")
    # per-row: sum of its 15 buckets == its 계 (rows are matched by order of the portfolio lists)
    if len(a["half0"]) == len(a["half1"]):
        for (l0, v0), (l1, v1) in zip(a["half0"], a["half1"]):
            if sum(v0) + sum(v1[:7]) != v1[7]:
                prob.append(f"row {l0}/{l1}: 15-bucket sum {sum(v0) + sum(v1[:7])} != 계 {v1[7]}")
    else:
        prob.append(f"half row counts differ {len(a['half0'])} vs {len(a['half1'])}")
    return prob
