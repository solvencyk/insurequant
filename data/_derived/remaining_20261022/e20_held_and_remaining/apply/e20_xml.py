# -*- coding: utf-8 -*-
"""e20 independent DART XML reader (no scripts/ or src/ imports; own code).  Generalised from KR0087_xml.py / stmt_lines.py of the round-18 evidence.
main_xml(code, fy)  -> Path of the main report xml of a (company, FY dir): the largest non-'_007' xml under data/dart/<fy>/raw/<code>_*/ (and its xml/ subdir)
read_statement(path, title_pat) -> (title_line, end_line, rows); rows = [dict(label=(text, line), tr_line, cells=[dict(acode, ctx, text, val, line, dec)])]
Lines are 1-based physical lines of the xml file (the citation unit used in every plan)."""
import re
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
RE_ATTR = re.compile(r'(ACODE|ACONTEXT|ADECIMAL)="([^"]*)"')
RE_P = re.compile(r"<P[^>]*>(.*?)</P>")
RE_TAG = re.compile(r"<[^>]+>")


def candidates(code, fy):
    base = ROOT / "data" / "dart" / fy / "raw"
    out = []
    for d in sorted(base.glob(f"{code}_*")):
        for p in list(d.glob("*.xml")) + list(d.glob("xml/*.xml")):
            if "_007" in p.name:
                continue
            out.append(p)
    return sorted(out, key=lambda p: p.stat().st_size, reverse=True)


def main_xml(code, fy):
    c = candidates(code, fy)
    if not c:
        raise FileNotFoundError(f"no xml for {code} {fy}")
    return c[0]


def rel(path):
    return str(Path(path).relative_to(ROOT)).replace("\\", "/")


def load_lines(path):
    return Path(path).read_text(encoding="utf-8", errors="replace").split("\n")


def find_titles(lines, pat):
    return [i for i, l in enumerate(lines, 1) if l.startswith("<TITLE") and re.search(pat, l)]


def num(t):
    t = t.replace(",", "").strip()
    if t in ("", "-"):
        return None
    neg = (t.startswith("(") and t.endswith(")")) or t.startswith("-") or t.startswith("\u25b3")
    t = t.strip("()-\u25b3 ")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def read_statement_at(lines, s):
    """statement table block that starts at title line s (1-based) and ends at the next <TITLE line"""
    e = len(lines)
    for i in range(s, len(lines)):
        if lines[i].startswith("<TITLE") and i + 1 > s:
            e = i + 1
            break
    rows, cur, i = [], None, s
    while i < e:
        l = lines[i]
        if l.startswith("<TR"):
            cur = {"label": None, "tr_line": i + 1, "cells": []}
        elif l.startswith("</TR"):
            if cur is not None and (cur["label"] is not None or cur["cells"]):
                rows.append(cur)
            cur = None
        elif cur is not None and (l.startswith("<TE") or l.startswith("<TH")):
            attrs = dict(RE_ATTR.findall(l))
            j, txt, pline = i + 1, [], None
            inline = re.search(r">([^<]*)</T[EH]>\s*$", l)
            if inline:
                txt.append(inline.group(1).replace("\u3000", " ").strip())
                pline = i + 1
                j = i
            while not inline and j < e and not lines[j].startswith("</TE") and not lines[j].startswith("</TH"):
                m = RE_P.search(lines[j])
                if m:
                    txt.append(RE_TAG.sub("", m.group(1)).replace("\u3000", " ").strip())
                    if pline is None:
                        pline = j + 1
                j += 1
            text = " ".join(txt).strip()
            if cur["label"] is None:
                cur["label"] = (text, pline)
            else:
                cur["cells"].append({"acode": attrs.get("ACODE"), "ctx": attrs.get("ACONTEXT", ""), "text": text, "val": num(text), "line": pline, "dec": attrs.get("ADECIMAL")})
            i = j
        i += 1
    return s, e, rows


def read_statement(path, title_pat=r"4-2\. 포괄손익계산서"):
    lines = load_lines(path)
    ts = find_titles(lines, title_pat)
    if not ts:
        raise KeyError(f"title {title_pat!r} not found in {path}")
    return read_statement_at(lines, ts[0])


def short_ctx(c):
    m = re.match(r"([CP]FY\d{4}d[A-Z]+)_", c)
    sep = "SEP" if "SeparateMember" in c else ("CON" if "ConsolidatedMember" in c else "---")
    return (m.group(1) if m else c[:20]) + ":" + sep


# ----------------------------------------------------------------------------- HTML-format filings (e.g. the 2026 half-year reports saved as plain HTML: <TD> cells, no ACONTEXT)
RE_MARK = re.compile(r"^<!-- ===== (\d+): (.*?) ===== -->")


def html_marker_range(lines, pat):
    """1-based (start, end) of the section whose '<!-- ===== N: title ===== -->' marker matches pat; end = line before the next marker"""
    s = None
    for i, l in enumerate(lines, 1):
        m = RE_MARK.match(l)
        if m:
            if s is not None:
                return s, i - 1
            if re.search(pat, m.group(2)):
                s = i
    return (s, len(lines)) if s is not None else (None, None)


def is_html_doc(lines):
    head = "\n".join(lines[:5])
    return "<HTML>" in head.upper()[:400] or "<!DOCTYPE HTML" in head.upper()


def read_html_rows(lines, lo, hi):
    """every <TR> of lines[lo..hi] (1-based) -> dict(tr_line, cells=[dict(text, val, line)]); cells = <TD|TH> contents (multi-line safe), first cell is the label"""
    rows, cur, cell = [], None, None
    OPEN = re.compile(r"<(TD|TH)\b[^>]*>", re.I)
    CLOSE = re.compile(r"</(TD|TH)>", re.I)
    for i in range(lo, min(hi, len(lines)) + 1):
        ln = lines[i - 1]
        if re.search(r"<TR\b", ln, re.I):
            cur = {"tr_line": i, "cells": []}
        if cur is None:
            continue
        pos = 0
        while pos < len(ln):
            if cell is None:
                m = OPEN.search(ln, pos)
                if not m:
                    break
                cell = {"text": [], "line": None, "start": i}
                pos = m.end()
            m2 = CLOSE.search(ln, pos)
            seg = ln[pos:m2.start()] if m2 else ln[pos:]
            t = re.sub(r"\s+", " ", RE_TAG.sub("", seg).replace("&nbsp;", " ")).strip()
            if t:
                cell["text"].append(t)
                if cell["line"] is None:
                    cell["line"] = i
            if m2:
                txt = " ".join(cell["text"]).replace("\u3000", " ").strip()
                cur["cells"].append({"text": txt, "val": num(txt), "line": cell["line"] or cell["start"]})
                cell = None
                pos = m2.end()
            else:
                break
        if re.search(r"</TR>", ln, re.I) and cur is not None:
            rows.append(cur)
            cur = None
    return rows
