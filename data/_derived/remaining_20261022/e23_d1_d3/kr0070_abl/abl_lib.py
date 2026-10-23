# -*- coding: utf-8 -*-
"""stdlib-only raw table machinery for the ABL (KR0070) independent re-read (own implementation, no repo module imported).
Lines are 1-based physical lines of the xml file split on '\n' (the convention used in every citation of this chain)."""
import re
import sys
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


def norm_label(s):
    s = nspace(s)
    s = re.sub(r"^([\u2160-\u2169]+|[IVX]+|\d+)\.", "", s)
    s = re.sub(r"^\(\d+\)", "", s)
    s = re.sub(r"\(주[^)]*\)", "", s)
    return s.replace("(손실)", "").replace("(수익)", "")


def parse_tr(L, i, j):
    """cells of the TR spanning physical lines i..j (0-based inclusive): [dict(tag, colspan, rowspan, text, line, ctx, acode)]  (blank cells included; line = physical line of the first text)"""
    out = []
    k = i
    while k <= j:
        m = re.match(r"\s*<(TD|TE|TH)\b([^>]*)>(.*)$", L[k], re.I)
        if m:
            attrs = m.group(2)
            cs = re.search(r'COLSPAN="(\d+)"', attrs, re.I)
            rs = re.search(r'ROWSPAN="(\d+)"', attrs, re.I)
            ctx = re.search(r'ACONTEXT="([^"]*)"', attrs, re.I)
            ac = re.search(r'ACODE="([^"]*)"', attrs, re.I)
            rest = m.group(3)
            base = dict(tag=m.group(1).upper(), colspan=int(cs.group(1)) if cs else 1, rowspan=int(rs.group(1)) if rs else 1, ctx=ctx.group(1) if ctx else "", acode=ac.group(1) if ac else "")
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
    """[(a, b)] 0-based inclusive bounds of every LEAF <TABLE>...</TABLE>"""
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


def titles(L):
    """[(0-based line, cleaned title text)] of every <TITLE ...> line"""
    return [(k, clean(s)) for k, s in enumerate(L) if s.startswith("<TITLE")]


def section_range(L, title_re):
    """(a, b) 0-based: from the first <TITLE> matching title_re to the next <TITLE>"""
    ts = titles(L)
    for n, (k, t) in enumerate(ts):
        if re.search(title_re, t):
            return k, (ts[n + 1][0] if n + 1 < len(ts) else len(L) - 1)
    raise RuntimeError(f"title {title_re!r} not found")


def unit_above(L, ln, span=400):
    """unit text '(단위 : 원|백만원|천원)' above 1-based line ln"""
    for k in range(ln - 1, max(ln - span, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", TAG.sub("", L[k]))
        if m:
            return m.group(1), k + 1
    return None, None


UNIT_MN = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0}
