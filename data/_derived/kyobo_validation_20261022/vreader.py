# -*- coding: utf-8 -*-
"""Minimal independent reader for DART XML: tables (start line, nearest preceding TITLE, rows of cell text)."""
import re, html, bisect
from pathlib import Path

TAG = re.compile(r"<[^>]+>")
TABLE = re.compile(r"<TABLE\b.*?</TABLE>", re.S)
TR = re.compile(r"<TR\b.*?</TR>", re.S)
CELL = re.compile(r"<(TD|TH|TE|TU)\b[^>]*>(.*?)</\1>", re.S)
TITLE = re.compile(r"<TITLE\b[^>]*>(.*?)</TITLE>", re.S)

def clean(s):
    s = TAG.sub("", s)
    s = html.unescape(s).replace("\xa0", " ").replace("\u3000", " ")
    return re.sub(r"\s+", " ", s).strip()

def num(s):
    s = s.strip().replace(",", "").replace(" ", "")
    if s in ("", "-", "―", "–"): return None
    neg = False
    if s.startswith("(") and s.endswith(")"): neg = True; s = s[1:-1]
    if s[:1] in ("△", "▲"): neg = True; s = s[1:]
    if s.startswith("-"): neg = True; s = s[1:]
    try: v = float(s)
    except ValueError: return None
    return -v if neg else v

def read_tables(path):
    txt = Path(path).read_text(encoding="utf-8")
    nl = [m.start() for m in re.finditer("\n", txt)]
    line = lambda pos: bisect.bisect_right(nl, pos) + 1
    titles = [(m.start(), clean(m.group(1))) for m in TITLE.finditer(txt)]
    tpos = [p for p, _ in titles]
    out = []
    for m in TABLE.finditer(txt):
        k = bisect.bisect_right(tpos, m.start()) - 1
        rows = []
        for r in TR.finditer(m.group(0)):
            cells = [clean(c.group(2)) for c in CELL.finditer(r.group(0))]
            rows.append({"line": line(m.start() + r.start()), "cells": cells})
        out.append({"line": line(m.start()), "title": titles[k][1] if k >= 0 else "", "rows": rows})
    return out
