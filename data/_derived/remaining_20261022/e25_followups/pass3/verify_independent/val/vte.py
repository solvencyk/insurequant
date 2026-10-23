# -*- coding: utf-8 -*-
"""Validation own reader for DART XML with <TE ACODE/ACONTEXT> cells (xbrl-tagged tables). Independent of parser."""
import re, sys, html
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val")
from vtab import clean, num

CELL_RE = re.compile(r"<(TE|TD|TH)\b([^>]*)>(.*?)</\1>", re.S | re.I)
ATTR = lambda a, k: (re.search(k + r'="([^"]*)"', a, re.I) or [None, None])[1]


def tagged_rows(path, a, b):
    """rows between line a and b: list of dict(line, labels[list of ko], eng[list], cells[list of (ctx, code, text)])"""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    seg = "\n".join(lines[a - 1:b])
    # line number of each TR start
    out = []
    pos = 0
    for m in re.finditer(r"<TR\b.*?</TR>", seg, re.S | re.I):
        ln = a + seg.count("\n", 0, m.start())
        row = m.group(0)
        labels, engs, cells = [], [], []
        for c in CELL_RE.finditer(row):
            attrs, inner = c.group(2), c.group(3)
            txt = clean(inner)
            ctx = ATTR(attrs, "ACONTEXT")
            if ctx:
                cells.append((ctx, ATTR(attrs, "ACODE"), txt))
            else:
                labels.append(txt)
                engs.append(ATTR(attrs, "ENG"))
        out.append(dict(line=ln, labels=labels, eng=engs, cells=cells))
    return out


def period_of(ctx):
    m = re.match(r"([CP])FY(\d{4})(d|e)?([A-Za-z]*)", ctx)
    if not m:
        return ctx[:12]
    return f"{m.group(1)}{m.group(2)}{m.group(3) or ''}{m.group(4)}"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    path, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    for r in tagged_rows(path, a, b):
        lab = " / ".join([l for l in r["labels"] if l.strip()])
        vals = " ; ".join(f"{period_of(c)}={t}" for c, _, t in r["cells"])
        print(f"L{r['line']} {lab} || {vals}")
