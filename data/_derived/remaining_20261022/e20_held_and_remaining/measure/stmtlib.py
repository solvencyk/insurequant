# -*- coding: utf-8 -*-
"""stmtlib: locate and read the SEPARATE-basis statement of comprehensive income of a DART filing with exact line numbers.
READ-ONLY.  Works for both XML dialects (new <TE>+ACODE, old <TD>)."""
from __future__ import annotations

import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

RE_NET = re.compile(r"(분기순이익|반기순이익|당기순이익|분기순손익|반기순손익|당기순손익|분기순손실|당기순손실)")


def titles(lines):
    out = []
    for i, l in enumerate(lines, 1):
        if l.startswith("<TITLE"):
            out.append((i, M.RE_TAG.sub("", l).strip()))
    return out


def sep_section(lines):
    """(start, end) line range of the separate-basis financial statements: from the 'N. 재무제표' (not 연결) TITLE to the next
    '재무제표 주석' TITLE.  Falls back to (0, len)."""
    ts = titles(lines)
    start = end = None
    for i, (ln, t) in enumerate(ts):
        tt = re.sub(r"\s+", "", t)
        if start is None and re.match(r"^\d+\.재무제표$", tt):
            start = ln
        elif start is not None and end is None and re.match(r"^\d+\.재무제표주석$", tt):
            end = ln
            break
    return (start or 0, end or len(lines))


def statement_tables(lines, require=("보험",)):
    """Tables inside the separate section that look like an income statement (a net-income row + the require tokens)."""
    s, e = sep_section(lines)
    out = []
    for t in M.iter_tables(lines):
        if not (s <= t["start"] <= e):
            continue
        labels = [M.norm_label(r["cells"][0]["text"]) for r in t["rows"] if r["cells"]]
        if any(RE_NET.search(l) for l in labels) and all(any(req in l for l in labels) for req in require):
            out.append(t)
    return out


def row_values(row, drop_note=True):
    """numeric value cells of a row (after the label), as [(val, line, text)].  The note-reference column (e.g. '29,30', '41') is
    dropped when the row carries one more cell than the others (detected by the caller via ncols)."""
    cells = row["cells"][1:]
    return [(c["val"], c["line"], c["text"]) for c in cells]


def read_statement(lines, table):
    """-> list of dict(label, tr_line, vals=[(val,line,text)...]) for rows with a label."""
    rows = []
    for r in table["rows"]:
        if not r["cells"]:
            continue
        label = r["cells"][0]["text"]
        vals = [(c["val"], c["line"], c["text"]) for c in r["cells"][1:]]
        rows.append({"label": label, "nlabel": M.norm_label(label), "tr_line": r["tr_line"], "vals": vals,
                     "label_line": r["cells"][0]["line"]})
    return rows


def value_cols(rows):
    """number of value columns = max count of numeric cells in a row (note column is non-numeric text or small ints)."""
    best = 0
    for r in rows:
        n = sum(1 for v in r["vals"] if v[0] is not None)
        best = max(best, n)
    return best


def prior_ytd(row, ncol=None):
    """the PRIOR-year cumulative cell of a quarterly/half-year statement row = last numeric cell."""
    nums = [v for v in row["vals"] if v[0] is not None]
    return nums[-1] if nums else None


def cur_ytd(row):
    """current-year cumulative cell: for [cur3m, curYTD, prev3m, prevYTD] it is the 2nd numeric cell; for 2-col [cur, prev] the 1st."""
    nums = [v for v in row["vals"] if v[0] is not None]
    if len(nums) >= 4:
        return nums[1]
    return nums[0] if nums else None
