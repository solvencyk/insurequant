# -*- coding: utf-8 -*-
"""Validation stage own table reader for DART XML (HTML-ish TABLE/TR/TD). No parser code reused."""
import re, sys, html

TD_RE = re.compile(r"<T[DHE]\b[^>]*>(.*?)</T[DHE]>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")


def clean(s):
    s = TAG_RE.sub("", s)
    s = html.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def num(s):
    """printed number -> float. (x) or <x> or negative sign => negative; dash => 0. None if not numeric."""
    t = s.replace(",", "").replace(" ", "")
    if t in ("-", "–", "—", ""):
        return 0.0 if t in ("-", "–", "—") else None
    neg = False
    m = re.fullmatch(r"[(\[<△▲](-?[0-9.]+)[)\]>]?", t)
    if m:
        neg = True
        t = m.group(1)
    elif t.startswith("-") or t.startswith("△") or t.startswith("▲"):
        neg = True
        t = t[1:]
    if not re.fullmatch(r"[0-9]+(\.[0-9]+)?", t):
        return None
    v = float(t)
    return -v if neg else v


def load_tables(path):
    """return list of (start_line, end_line, rows) where rows=[[cell text,...]]"""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    tabs = []
    cur = None
    depth = 0
    buf = []
    start = 0
    for i, ln in enumerate(lines, 1):
        up = ln.upper()
        nopen = len(re.findall(r"<TABLE[\s>]", up))
        nclose = up.count("</TABLE>")
        if nopen:
            if depth == 0:
                start = i
                buf = []
            depth += nopen
        if depth > 0:
            buf.append(ln)
        if nclose and depth > 0:
            depth -= nclose
            if depth <= 0:
                depth = 0
                txt = "\n".join(buf)
                rows = []
                # rows with line numbers: split on <TR
                parts = re.split(r"<TR\b", txt, flags=re.I)[1:]
                for p in parts:
                    cells = [clean(c) for c in TD_RE.findall(p)]
                    if cells:
                        rows.append(cells)
                tabs.append((start, i, rows))
    return tabs, lines


def dump(path, a, b, lines=None):
    tabs, _ = load_tables(path)
    for s, e, rows in tabs:
        if s >= a and s <= b:
            print(f"--- table L{s}-L{e}")
            for r in rows:
                print(" | ".join(r))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    dump(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
