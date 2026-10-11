# -*- coding: utf-8 -*-
"""Generalised reader for the CSM roll-forward note ("측정요소별 변동내역", unit 천원) of the Lina Life (KR0074) management-disclosure PDFs.

Why a second reader (the first one, in extract_lina_csm_rows_20261011.py, counts 6 numeric tokens per row): the older filings
print the same note with other column structures and blank cells, so a cell cannot be identified by its position in the token list.
This reader assigns every numeric token to a column by the RIGHT EDGE of the token (numbers are right aligned in their cell) using
the 기초 잔액 row (all cells filled) as the column ruler, so blank cells stay None.

Column generations seen (Lina):
  G1  FY2023_Qx own filing (old basis)        5 columns  PV | RA | CSM (one column) | IACF asset | total
  G1' FY2024_Q1/Q2 prior-period column         7 columns  PV | RA | CSM FVA | CSM MRA | CSM post | IACF asset | total   (old basis)
  G3  FY2024_Q1..Q3 own, FY2024_Q3 prior, FY2025/26 6 columns  PV | RA | CSM FVA | CSM MRA | CSM post | total
CSM columns = every column between RA and the IACF-asset/total columns.

Row keys (normalised labels, see LABELS): the vertical identity open + fut + cur + inc + iacf_imp + cf + fin + other = close must hold
exactly in every CSM column and within +-TOTAL_TOL 천원 in the other columns (the old-format total column is a sum of rounded cells).
"""
from __future__ import annotations

import re

NUM_RE = re.compile(r"^\(?-?[\d,]+(?:\.\d+)?\)?$")
DASHES = {"-", "–", "—", "−"}
TOTAL_TOL = 2          # 천원, non-CSM columns of the old formats (rounding of the total column)

LABELS = {
    "open": ("기초잔액",),
    "fut": ("미래서비스관련변동",),
    "adj": ("보험계약마진조정하는추정치의변동분",),
    "onerous": ("손실부담계약집합의손실(환입)",),
    "new": ("최초인식한계약의효과",),
    "cur": ("현행서비스관련변동",),
    "amort": ("제공한서비스반영인식한보험계약마진",),
    "rarel": ("위험해제에대한위험조정의변동분",),
    "exp": ("경험조정",),
    "inc": ("발생사고부채이행현금흐름변동",),
    "iacf_imp": ("보험취득현금흐름자산손상차손(환입)",),
    "cf": ("현금흐름",),
    "fin": ("보험금융손익",),
    "fin_pl": ("당기손익인식",),
    "fin_oci": ("기타포괄손익인식",),
    "other": ("기타",),
    "close": ("기말잔액", "분기말잔액", "반기말잔액"),
}
VERTICAL = ("open", "fut", "cur", "inc", "iacf_imp", "cf", "fin", "other")     # summed into close (absent rows count as 0)


def norm(s: str) -> str:
    return re.sub(r"[\s　]+", "", s)


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
    """rows of (x0, x1, text), sorted by y then x."""
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


def split_row_x(row):
    """-> (label_norm, [(x1, token), ...]) numeric tokens with their right edges."""
    parts, nums, seen = [], [], False
    for _x0, x1, t in row:
        if is_num_token(t):
            seen = True
            nums.append((x1, t))
        elif not seen:
            parts.append(t)
        else:
            parts.append("\u0001" + t)
    return norm("".join(parts)), nums


def read_note(page):
    """Read one roll-forward page.

    -> dict(ncols, edges, rows={key: [int|None]*ncols}, dup=[...], ambiguous=[...], ruler_tokens=n)
    The ruler is the first 기초잔액 row that has >= 5 numeric tokens."""
    prepared = [(lab, nums) for lab, nums in (split_row_x(r) for r in page_rows(page)) if nums]
    ri = next((i for i, (lab, nums) in enumerate(prepared) if lab == "기초잔액" and len(nums) >= 5), None)
    if ri is None:
        return {"ncols": 0, "edges": [], "rows": {}, "dup": [], "ambiguous": ["no 기초잔액 ruler row"]}
    ruler = prepared[ri]
    edges = [x1 for x1, _ in ruler[1]]
    pitch = min(b - a for a, b in zip(edges, edges[1:]))
    half = 0.5 * pitch
    rows, dup, amb = {}, [], []
    for lab, nums in prepared[ri:]:                # only the table that starts at the ruler row, up to its first closing row
        key = next((k for k, variants in LABELS.items() if lab in variants), None)
        if key is None:
            continue
        cells, used = [None] * len(edges), set()
        ok = True
        if len(nums) == len(edges):                 # a full row: one token per column, in order (dash cells sit at other x than digits)
            cells = [to_int(t) for _x1, t in nums]
        else:                                       # a row with blank cells: place every token by its right edge
            for x1, t in nums:
                j = min(range(len(edges)), key=lambda i: abs(edges[i] - x1))
                if abs(edges[j] - x1) > half or j in used:
                    ok = False
                    break
                used.add(j)
                cells[j] = to_int(t)
        if not ok:
            amb.append((key, lab, [t for _, t in nums]))
            continue
        if key in rows:
            dup.append(key)
        else:
            rows[key] = cells
        if key == "close":
            break
    return {"ncols": len(edges), "edges": [round(e, 1) for e in edges], "rows": rows, "dup": dup, "ambiguous": amb}


def csm_columns(ncols: int):
    """column indexes that hold CSM: G1 (5 cols) -> [2]; G1' (7 cols) -> [2,3,4]; G3 (6 cols) -> [2,3,4]."""
    return [2] if ncols == 5 else [2, 3, 4]


def total_col(ncols: int) -> int:
    return ncols - 1


def check_note(rd: dict, csm_tol: int = 0) -> list:
    """problems (empty = clean).  Exact (csm_tol=0) in the CSM columns, +-TOTAL_TOL in the others; horizontal sum within +-TOTAL_TOL.

    csm_tol=1 is used ONLY for the old-basis (pre-restatement) pages that are staged as holds: those printed tables carry a
    1 천원 rounding residual in a CSM column (FY2024_Q1 p52, FY2023_Q2 p84)."""
    prob = []
    rows, n = rd["rows"], rd["ncols"]
    if rd["ambiguous"]:
        prob.append(f"ambiguous rows {rd['ambiguous'][:2]}")
    if rd["dup"]:
        prob.append(f"duplicate labels {rd['dup']}")
    for k in ("open", "fut", "cur", "inc", "cf", "fin", "close", "new", "adj", "amort"):
        if k not in rows:
            prob.append(f"missing row {k}")
    if prob:
        return prob
    z = lambda v: 0 if v is None else v          # noqa: E731
    cs = csm_columns(n)
    # horizontal (columns before the total add up to the total): exact for CSM-bearing rows' CSM part is not defined, so +-TOL
    for k, v in rows.items():
        if abs(sum(z(x) for x in v[:-1]) - z(v[-1])) > TOTAL_TOL:
            prob.append(f"row {k}: components {sum(z(x) for x in v[:-1])} != total {z(v[-1])}")
    # vertical roll-forward per column
    for j in range(n):
        s = sum(z(rows[k][j]) for k in VERTICAL if k in rows)
        tol = csm_tol if j in cs else TOTAL_TOL
        if abs(s - z(rows["close"][j])) > tol:
            prob.append(f"column {j}{' (CSM)' if j in cs else ''}: roll-forward {s} != close {z(rows['close'][j])}")
    # sub-row identities
    for j in range(n):
        tol = csm_tol if j in cs else TOTAL_TOL
        if "onerous" in rows and abs(z(rows["adj"][j]) + z(rows["onerous"][j]) + z(rows["new"][j]) - z(rows["fut"][j])) > tol:
            prob.append(f"column {j}: 미래서비스 sub-rows")
        if "rarel" in rows and "exp" in rows and abs(z(rows["amort"][j]) + z(rows["rarel"][j]) + z(rows["exp"][j]) - z(rows["cur"][j])) > tol:
            prob.append(f"column {j}: 현행서비스 sub-rows")
        if "fin_pl" in rows and "fin_oci" in rows and abs(z(rows["fin_pl"][j]) + z(rows["fin_oci"][j]) - z(rows["fin"][j])) > tol:
            prob.append(f"column {j}: 보험금융손익 sub-rows")
    return prob


def read_amort_page(page) -> dict:
    """Expected-CSM-amortisation schedule (yearly format, two stacked half-tables, 8 numbers per row).  Same logic as the first reader."""
    halves, totals, half = [[], []], [None, None], 0
    for r in page_rows(page):
        parts, nums, seen = [], [], False
        for _x0, _x1, t in r:
            if is_num_token(t):
                seen = True
                nums.append(t)
            elif not seen:
                parts.append(t)
        lab = norm("".join(parts))
        if len(nums) != 8:
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
            if sum(v[j] for _, v in a[key]) != tot[j]:
                prob.append(f"half{h} col {j}: portfolio sum != 합계")
    if sum(a["total0"]) + sum(a["total1"][:7]) != a["total1"][7]:
        prob.append("15 buckets do not add up to the printed 계")
    if len(a["half0"]) != len(a["half1"]):
        prob.append("half row counts differ")
    else:
        for (l0, v0), (_l1, v1) in zip(a["half0"], a["half1"]):
            if sum(v0) + sum(v1[:7]) != v1[7]:
                prob.append(f"row {l0}: 15-bucket sum != 계")
    return prob


def read_coarse_schedule(page) -> dict:
    """Coarse expected-CSM-amortisation table of the 2023/2024 interim filings: the first row with 6 numbers =
    1년 이내 | 1년 초과 3년 이하 | 3년 초과 5년 이하 | 5년 초과 10년 이하 | 10년 초과 | 합계 (천원), period-end column."""
    for r in page_rows(page):
        _lab, nums = split_row_x(r)
        if len(nums) == 6:
            v = [to_int(t) for _x1, t in nums]
            return {"buckets": v[:5], "total": v[5], "sum_ok": sum(v[:5]) == v[5]}
    return {"buckets": None, "total": None, "sum_ok": False}


def csm_residual(items: dict) -> int:
    """open + new + fin + adj + amort + other - close of the summed CSM items (천원); 0 for every restated-basis page."""
    return items["open"] + items["new"] + items["fin"] + items["adj"] + items["amort"] + items.get("other", 0) - items["close"]


def csm_items(rd: dict) -> dict:
    """the six CSM items (sum over the CSM columns), 천원, plus `other` = the CSM part of the 기타(미결계정변동) row (0 when absent)."""
    rows, cs = rd["rows"], csm_columns(rd["ncols"])
    s = lambda k: sum(0 if rows[k][j] is None else rows[k][j] for j in cs) if k in rows else 0   # noqa: E731
    return {"open": s("open"), "new": s("new"), "fin": s("fin"), "adj": s("adj"), "amort": s("amort"), "close": s("close"), "other": s("other")}


def sum_items(parts: dict) -> dict:
    keys = ("open", "new", "fin", "adj", "amort", "close", "other")
    return {k: sum(v[k] for v in parts.values()) for k in keys}
