"""Read-only helper: parse a DART XML into tables with raw line numbers.

Each table -> dict(start, end, caption, unit, header_rows, rows)
  rows: list of (tr_line, [cell_text...], [cell_line...])
Used only for evidence extraction (KR0073 CSM basis/vintage fix, 2026-10-21).
"""
import re
import sys

TAG_RE = re.compile(r"<[^>]+>")
CELL_RE = re.compile(r"<(TD|TH|TE|TU)\b[^>]*>(.*?)</\1>", re.S)
P_RE = re.compile(r"<P\b[^>]*>(.*?)</P>", re.S)
TITLE_RE = re.compile(r"<TITLE\b[^>]*>(.*?)</TITLE>", re.S)


def clean(s):
    s = TAG_RE.sub("", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", s).strip()


def read_lines(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().split("\n")


def parse_tables(path, lines=None):
    """Return (tables, titles) where titles = [(line_no, text)]."""
    if lines is None:
        lines = read_lines(path)
    tables = []
    titles = []
    last_caption = ""
    last_caption_line = 0
    cur = None
    row = None
    in_thead = False
    for i, ln in enumerate(lines, start=1):
        m = TITLE_RE.search(ln)
        if m:
            titles.append((i, clean(m.group(1))))
        if cur is None:
            for pm in P_RE.finditer(ln):
                t = clean(pm.group(1))
                if t:
                    last_caption = t
                    last_caption_line = i
            if "<TABLE" in ln:
                cur = {
                    "start": i,
                    "caption": last_caption,
                    "caption_line": last_caption_line,
                    "unit": "",
                    "header_rows": [],
                    "rows": [],
                }
                in_thead = False
            continue
        # inside a table
        if "<THEAD" in ln:
            in_thead = True
        if "</THEAD" in ln:
            in_thead = False
        if "<TR" in ln:
            row = {"line": i, "cells": [], "lines": []}
        for cm in CELL_RE.finditer(ln):
            if row is None:
                continue
            row["cells"].append(clean(cm.group(2)))
            row["lines"].append(i)
        if "</TR>" in ln and row is not None:
            texts = row["cells"]
            if texts:
                joined = " ".join(texts)
                if "단위" in joined and not cur["unit"]:
                    cur["unit"] = joined
                if in_thead:
                    cur["header_rows"].append((row["line"], texts, row["lines"]))
                else:
                    cur["rows"].append((row["line"], texts, row["lines"]))
            row = None
        if "</TABLE>" in ln:
            cur["end"] = i
            tables.append(cur)
            cur = None
            row = None
    return tables, titles


def num(s):
    """Parse a DART numeric cell: '(1,234)' -> -1234, '-' -> 0, '' -> None."""
    s = s.strip().replace(",", "").replace("△", "-")
    if s in ("-", "−", "–"):
        return 0
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    path = sys.argv[1]
    tabs, titles = parse_tables(path)
    print(len(tabs), "tables;", len(titles), "titles")
