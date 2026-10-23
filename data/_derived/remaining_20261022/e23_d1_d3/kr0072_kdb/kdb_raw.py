# -*- coding: utf-8 -*-
"""KR0072 raw-XML machinery used ONLY by kr0072_verify.py (independent re-read).  Standard library only: no e21_* / e23_* / scripts / src import, so it cannot share a defect with the planner.
Everything here works on the physical lines of the DART XML (1-based line numbers are what the plan cites)."""
import re
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
TAG = re.compile(r"<[^>]+>")
_cache = {}


def lines_of(rel):
    if rel not in _cache:
        _cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return _cache[rel]


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("\u3000", " ").replace("\xa0", " ")).strip()


def nspace(s):
    return re.sub(r"\s+", "", (s or "").replace("\u3000", ""))


def parse_num(t):
    t = (t or "").strip().replace(",", "").replace(" ", "")
    if t == "":
        return None
    if t in ("-", "\u2212"):
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    t2 = t.strip("()")
    try:
        v = float(t2)
    except ValueError:
        return None
    return -v if neg else v


def parse_tr(L, i, j):
    """cells of the TR spanning physical lines i..j (0-based inclusive): [dict(tag, colspan, rowspan, text, line)]  (line = physical line of the first text)"""
    out = []
    k = i
    while k <= j:
        m = re.match(r"\s*<(TD|TE|TH)\b([^>]*)>(.*)$", L[k], re.I)
        if m:
            attrs = m.group(2)
            cs = re.search(r'COLSPAN="(\d+)"', attrs, re.I)
            rs = re.search(r'ROWSPAN="(\d+)"', attrs, re.I)
            rest = m.group(3)
            base = dict(tag=m.group(1).upper(), colspan=int(cs.group(1)) if cs else 1, rowspan=int(rs.group(1)) if rs else 1, attrs=attrs)
            if re.search(r"</(TD|TE|TH)>\s*$", rest, re.I):
                out.append(dict(base, text=clean(rest), line=k + 1))
            else:
                buf, tl, q = ([clean(rest)] if clean(rest) else []), (k + 1 if clean(rest) else None), k + 1
                while q <= j and not re.match(r"\s*</(TD|TE|TH)", L[q], re.I):
                    t = clean(L[q])
                    if t:
                        buf.append(t)
                        if tl is None:
                            tl = q + 1
                    q += 1
                out.append(dict(base, text=" ".join(buf).strip(), line=tl or (k + 1)))
                k = q
        k += 1
    return out


def table_rows(L, a, b):
    """all <TR> of the table spanning lines a..b (0-based): [dict(tr, cells)]"""
    rows, k = [], a
    while k <= b:
        if re.match(r"\s*<TR\b", L[k], re.I):
            j = k
            while not re.match(r"\s*</TR", L[j], re.I):
                j += 1
            rows.append(dict(tr=k + 1, cells=parse_tr(L, k, j)))
            k = j
        k += 1
    return rows


def all_tables(L):
    """[(a, b)] 0-based inclusive bounds of every LEAF <TABLE>...</TABLE> (tables that contain another table are skipped)"""
    out, stack = [], []
    for k, s in enumerate(L):
        if re.match(r"\s*<TABLE\b", s, re.I):
            if stack:
                stack[-1][1] = True
            stack.append([k, False])
        elif re.match(r"\s*</TABLE", s, re.I) and stack:
            a, has_child = stack.pop()
            if not has_child:
                out.append((a, k))
    return out


def header_paths(L, a, b):
    """logical column index -> header path (texts top to bottom, consecutive repeats removed) from the THEAD of the table a..b (None when the table has no THEAD)"""
    h0 = next((k for k in range(a, b + 1) if re.match(r"\s*<THEAD", L[k], re.I)), None)
    h1 = next((k for k in range(h0 or a, b + 1) if re.match(r"\s*</THEAD", L[k], re.I)), None)
    if h0 is None or h1 is None:
        return None
    trs, k = [], h0
    while k <= h1:
        if re.match(r"\s*<TR", L[k], re.I):
            i0 = k
            while not re.match(r"\s*</TR", L[k], re.I):
                k += 1
            trs.append((i0, k))
        k += 1
    grid, occ, ncols = {}, set(), 0
    for r, (i0, j0) in enumerate(trs):
        col = 0
        for c in parse_tr(L, i0, j0):
            while (r, col) in occ:
                col += 1
            for dr in range(c["rowspan"]):
                for dc in range(c["colspan"]):
                    occ.add((r + dr, col + dc))
                    grid[(r + dr, col + dc)] = c["text"]
            col += c["colspan"]
        ncols = max(ncols, col)
    paths = []
    for col in range(ncols):
        path = []
        for r in range(len(trs)):
            t = grid.get((r, col))
            if t is not None and (not path or path[-1] != t):
                path.append(t)
        paths.append(path)
    return paths


def body_rows(L, a, b):
    """rows after </THEAD> (or all rows when there is no THEAD)"""
    h1 = next((k for k in range(a, b + 1) if re.match(r"\s*</THEAD", L[k], re.I)), None)
    rows = table_rows(L, a, b)
    return [r for r in rows if h1 is None or r["tr"] - 1 > h1]


def titles(L):
    return [(k, clean(s)) for k, s in enumerate(L) if s.startswith("<TITLE")]


def section(L, title_re, nth=0):
    """(a, b) 0-based: from the nth <TITLE> matching title_re to the next <TITLE> of ANY kind"""
    ts = titles(L)
    hits = [n for n, (k, t) in enumerate(ts) if re.search(title_re, t)]
    if len(hits) <= nth:
        raise RuntimeError(f"title {title_re!r} (#{nth}) not found")
    n = hits[nth]
    return ts[n][0], (ts[n + 1][0] if n + 1 < len(ts) else len(L) - 1)


def unit_above(L, ln, span=400):
    """'(단위 : 원|백만원|천원)' / '(단위:백만원)' nearest above 1-based line ln -> (unit, 1-based line)"""
    for k in range(ln - 1, max(ln - span, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", TAG.sub("", L[k]))
        if m:
            return m.group(1), k + 1
    return None, None


UNIT_MN = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0}


def mn(printed, unit):
    v = parse_num(printed)
    return None if v is None else v * UNIT_MN[unit]


def close(a, b, tol=2e-6):
    return a is not None and b is not None and abs(a - b) <= tol


def table_bounds_at(L, line1):
    """(a, b) 0-based of the <TABLE> that starts exactly at 1-based line `line1`"""
    a = line1 - 1
    if not re.match(r"\s*<TABLE\b", L[a], re.I):
        raise RuntimeError(f"line {line1} is not a <TABLE> start: {L[a][:60]!r}")
    depth = 0
    for k in range(a, len(L)):
        if re.match(r"\s*<TABLE\b", L[k], re.I):
            depth += 1
        if re.match(r"\s*</TABLE", L[k], re.I):
            depth -= 1
            if depth == 0:
                return a, k
    raise RuntimeError("unterminated table")


def preceding_text(L, a, n=3, span=80):
    """the nearest n non-empty plain-text lines (outside tags) above 0-based line a: [(1-based line, text)]"""
    out, k = [], a - 1
    while k >= 0 and len(out) < n and a - k <= span:
        t = clean(L[k])
        if t and not re.match(r"^<", L[k].strip()) or (t and L[k].strip().startswith("<P")):
            out.append((k + 1, t))
        k -= 1
    return out


def table_unit(L, a, b, rows=None):
    """unit of the table spanning 0-based lines a..b: the '(단위 : X)' text INSIDE the table (first rows / THEAD) wins; else the nearest one above the table.  -> (unit, 1-based line, 'in' | 'above')"""
    for k in range(a, min(b, a + 80) + 1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", TAG.sub("", L[k]))
        if m:
            return m.group(1), k + 1, "in"
    un, ln = unit_above(L, a + 1, span=200)
    return un, ln, "above"
