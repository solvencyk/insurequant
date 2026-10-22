# -*- coding: utf-8 -*-
"""e20 reader for the 2023 quarterly/half-year layout of DB생명 (KR0082): plain <TABLE> under '4. 재무제표' with caption '분 기 포 괄 손 익 계 산 서' / '반 기 포 괄 손 익 계 산 서',
rows 'I. 보험서비스손익', ' 1. 보험손익', '  (3) 기타사업비', 'II. 투자손익', 'III. 보험금융손익' ...; every period has a (sub, total) pair of cells (parents print in the total cell).
Q1: groups [cur, prior]; H1: groups [cur 3M, cur cum, prior 3M, prior cum].  Unit 원.  Returns rows with the physical line of the value cell."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_xml as X  # noqa: E402

RE_TD = re.compile(r"<(TD|TH)\b[^>]*>(.*?)</(TD|TH)>", re.S)


def clean(s):
    return re.sub(r"\s+", " ", X.RE_TAG.sub("", s).replace("&nbsp;", " ")).replace("　", " ").strip()


def read_table(path, caption_pat, start_after=1):
    """first TABLE (after line start_after) whose caption cell matches caption_pat -> (caption_line, rows) with rows = [dict(label, tr_line, cells=[(text, line)])] of the NEXT table with a THEAD (the data table)"""
    lines = X.load_lines(path)
    cap = None
    for i, l in enumerate(lines, 1):
        if i >= start_after and re.search(caption_pat, clean(l)) and "<TD" in l:
            cap = i
            break
    if cap is None:
        raise KeyError(f"caption {caption_pat!r} not found in {path}")
    # the data table starts at the next '<THEAD' ; ends at the next '</TABLE>'
    i = cap
    while i < len(lines) and "<THEAD" not in lines[i]:
        i += 1
    j = i
    while j < len(lines) and "</TABLE>" not in lines[j]:
        j += 1
    rows, cur = [], None
    for k in range(i, j + 1):
        l = lines[k]
        if "<TR" in l:
            cur = {"tr_line": k + 1, "cells": []}
        if cur is not None:
            for m in re.finditer(r"<(TD|TH)\b[^>]*>(.*?)</(TD|TH)>", l):
                cur["cells"].append((clean(m.group(2)), k + 1))
            if "</TR>" in l:
                rows.append(cur)
                cur = None
    return cap, [dict(label=r["cells"][0][0], label_line=r["cells"][0][1], tr_line=r["tr_line"], cells=r["cells"][1:]) for r in rows if r["cells"]]


def group_value(cells, g):
    """value of period group g: first non-blank cell among (2g, 2g+1)"""
    for idx in (2 * g, 2 * g + 1):
        if idx < len(cells) and cells[idx][0] not in ("", "　"):
            return X.num(cells[idx][0]), cells[idx][1], cells[idx][0]
    return None, None, None


def norm_label(s):
    return re.sub(r"\s+", "", s)
