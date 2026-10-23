# -*- coding: utf-8 -*-
import re, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e23_read as E
import e21_t2 as T
M = T.M
_orig_read_lines = M.read_lines
def _rl(p):
    return [l.lstrip() for l in _orig_read_lines(p)]
M.read_lines = _rl   # plain-HTML filings (2026) indent <TD>/<TR>; physical line numbers are unchanged

def sep_start2(lines):
    s0 = T.sep_notes_from(lines)
    if s0:
        return s0
    for i, l in enumerate(lines, 1):
        m = re.match(r"^<!-- ===== \d+: (.*?) ===== -->", l)
        if m and re.match(r"^(\d+\.\s*)?재무제표\s*주석", m.group(1).strip()) and "연결" not in m.group(1):
            return i
    return 0

def tables_sep2(path):
    lines = M.read_lines(path)
    s0 = sep_start2(lines)
    out = []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        out.append((t, E.rows_full23(lines, t["start"], t["end"])))
    return lines, s0, out
