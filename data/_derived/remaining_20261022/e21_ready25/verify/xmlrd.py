# -*- coding: utf-8 -*-
"""Independent DART XML table reader for the validation re-read (does NOT import scripts/ or src/)."""
import re, bisect, html

_cache = {}
TAG = re.compile(r"<(/?)([A-Z][A-Z0-9\-]*)([^>]*)>")


def strip(s):
    s = re.sub(r"</?[A-Za-z][^>]*>", "", s)
    s = html.unescape(s)
    s = s.replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


class Doc:
    def __init__(self, path):
        self.path = path
        with open(path, encoding="utf-8", errors="replace") as f:
            self.text = f.read()
        t = self.text
        # line starts
        self.nl = [m.start() for m in re.finditer("\n", t)]
        self.titles = []  # (pos, line, text)
        for m in re.finditer(r"<TITLE[^>]*>(.*?)</TITLE>", t, re.S):
            self.titles.append((m.start(), self.line(m.start()), strip(m.group(1))))
        self.tables = []
        for m in re.finditer(r"<TABLE\b[^>]*>(.*?)</TABLE>", t, re.S):
            self.tables.append(self._parse_table(m))

    def line(self, pos):
        return bisect.bisect_right(self.nl, pos - 1) + 1

    def _parse_table(self, m):
        body = m.group(1)
        base = m.start(1)
        rows = []
        for rm in re.finditer(r"<TR\b[^>]*>(.*?)</TR>", body, re.S):
            cells = []
            for cm in re.finditer(r"<(TD|TE|TH|TU)\b([^>]*)>(.*?)</\1>", rm.group(1), re.S):
                attrs = cm.group(2)
                cs = re.search(r'COLSPAN="(\d+)"', attrs)
                txt = strip(cm.group(3))
                cells.append({"t": txt, "line": self.line(base + rm.start(1) + cm.start()), "end": self.line(base + rm.start(1) + cm.end()), "span": int(cs.group(1)) if cs else 1,
                              "tag": cm.group(1)})
            rows.append({"line": self.line(base + rm.start()), "cells": cells})
        return {"start": self.line(m.start()), "end": self.line(m.end()), "pos": m.start(), "rows": rows}

    def title_before(self, pos):
        i = bisect.bisect_right([t[0] for t in self.titles], pos) - 1
        return self.titles[i] if i >= 0 else None

    def titles_before(self, pos, n=3):
        i = bisect.bisect_right([t[0] for t in self.titles], pos) - 1
        return [self.titles[j] for j in range(max(0, i - n + 1), i + 1)]

    def table_at_line(self, ln):
        for ti, t in enumerate(self.tables):
            if t["start"] <= ln <= t["end"]:
                return ti, t
        return None, None

    def unit_before(self, t, window=6000):
        """nearest '단위' text before the table (or inside its first rows)."""
        seg = self.text[max(0, t["pos"] - window):t["pos"]]
        ms = list(re.finditer(r"단위\s*:?\s*([가-힣A-Za-z0-9,\s]+?)\s*\)", strip(seg)))
        # also search in the table's first 3 rows
        inner = " ".join(c["t"] for r in t["rows"][:4] for c in r["cells"])
        mi = re.search(r"단위\s*:?\s*([가-힣A-Za-z0-9,\s]+?)\s*\)", inner)
        if mi:
            return mi.group(1).strip()
        return ms[-1].group(1).strip() if ms else None


def get(path):
    if path not in _cache:
        _cache[path] = Doc(path)
    return _cache[path]


NUM = re.compile(r"^\(?\s*-?[\d,]+(\.\d+)?\s*\)?$|^[△▲]\s*[\d,]+(\.\d+)?$")


def parse_num(s):
    """printed text -> float or None. parentheses / triangle / leading minus = negative; '-' = 0."""
    s = s.strip()
    if s in ("-", "－", "—", ""):
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    if s and s[0] in "△▲":
        neg = True
        s = s[1:].strip()
    if s.startswith("-"):
        neg = True
        s = s[1:].strip()
    s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def row_at_line(doc, ln):
    ti, t = doc.table_at_line(ln)
    if t is None:
        return None
    for r in t["rows"]:
        for c in r["cells"]:
            if c["line"] <= ln <= c["end"]:
                return ti, t, r, c
    return None


UNIT_DIV = {"원": 1e6, "천원": 1e3, "백만원": 1.0, "억원": 1e-2, "백만 원": 1.0}


def unit_div(u):
    if u is None:
        return None
    u = u.replace(" ", "")
    return UNIT_DIV.get(u)
