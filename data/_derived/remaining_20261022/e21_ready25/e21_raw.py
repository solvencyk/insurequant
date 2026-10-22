# -*- coding: utf-8 -*-
"""e21 raw table-row reader that keeps ALL text of a cell (SPAN / P / plain text alike) and the physical line of the first text character.
The measure-phase mlib.iter_tables keeps only <P> text (labels wrapped in <SPAN> come out blank); this module re-reads a table range given by mlib (start..end, 1-based physical lines).
rows_full(lines, start, end) -> [dict(tr_line, cells=[dict(text, val, line)])]"""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M  # noqa: E402

TAG = re.compile(r"<[^>]+>")
CELL_OPEN = re.compile(r"^<T[DEH]\b", re.I)
CELL_CLOSE = re.compile(r"^</T[DEH]", re.I)


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ").replace("&amp;", "&").replace("\u3000", " ").replace("\xa0", " ")).strip()


def rows_full(lines, start, end):
    rows, cur = [], None
    j = start - 1
    last = min(end, len(lines))
    while j < last:
        l = lines[j]
        if l.startswith("<TR"):
            cur = {"tr_line": j + 1, "cells": []}
        elif l.startswith("</TR"):
            if cur is not None and cur["cells"]:
                rows.append(cur)
            cur = None
        elif cur is not None and CELL_OPEN.match(l):
            if re.search(r"</T[DEH]>\s*$", l, re.I):
                text, ln = clean(l), j + 1
                nj = j
            else:
                parts, ln, k = [], None, j + 1
                while k < last and not CELL_CLOSE.match(lines[k]):
                    t = clean(lines[k])
                    if t:
                        parts.append(t)
                        if ln is None:
                            ln = k + 1
                    k += 1
                text = " ".join(parts).strip()
                ln = ln or (j + 1)
                nj = k
            cur["cells"].append({"text": text, "val": M.num(text), "line": ln})
            j = nj
        j += 1
    return rows


def label_of(row):
    """text of the first cell that carries letters (the row label)"""
    for c in row["cells"]:
        if re.search(r"[가-힣A-Za-z]", c["text"]):
            return c["text"]
    return ""


def numeric_cells(row, skip=1):
    """numeric cells of a row after the first `skip` label cells: '-' counts as 0"""
    out = []
    for c in row["cells"][skip:]:
        if c["val"] is not None:
            out.append((c["val"], c["line"], c["text"]))
        elif c["text"].strip() in ("-", "−"):
            out.append((0.0, c["line"], c["text"]))
    return out
