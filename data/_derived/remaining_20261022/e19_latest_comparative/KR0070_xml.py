# -*- coding: utf-8 -*-
"""KR0070 independent XML reader (no scripts/ or src/ imports).  Reads the SEPARATE-basis statement of comprehensive income
(title '4-2. 포괄손익계산서') of a DART filing: for every <TR> the first <TE> label and every value <TE> (ACODE, ACONTEXT, text, line of the <P> value)."""
import re
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
FILES = {
 "FY2023_Q4": "data/dart/FY2023_Q4/raw/KR0070_에이비엘생명보험_20240329001518/xml/20240329001518.xml",
 "FY2024_Q1": "data/dart/FY2024_Q1/raw/KR0070_에이비엘생명보험/20240516002045.xml",
 "FY2024_Q2": "data/dart/FY2024_Q2/raw/KR0070_에이비엘생명보험/20240814004092.xml",
 "FY2024_Q3": "data/dart/FY2024_Q3/raw/KR0070_에이비엘생명보험/20241114002738.xml",
 "FY2024_Q4": "data/dart/FY2024_Q4/raw/KR0070_에이비엘생명보험_20250331001358/20250331001358.xml",
 "FY2025_Q1": "data/dart/FY2025_Q1/raw/KR0070_에이비엘생명보험/20250515002435.xml",
 "FY2025_Q2": "data/dart/FY2025_Q2/raw/KR0070_에이비엘생명보험/20250814004404.xml",
 "FY2025_Q3": "data/dart/FY2025_Q3/raw/KR0070_에이비엘생명보험/20251114002593.xml",
 "FY2025_Q4": "data/dart/FY2025_Q4/raw/KR0070_에이비엘생명보험_20260331003080/20260331003080.xml",
}
RE_ATTR = re.compile(r'(ACODE|ACONTEXT|ADECIMAL)="([^"]*)"')
RE_P = re.compile(r"<P[^>]*>(.*?)</P>")
RE_TAG = re.compile(r"<[^>]+>")

def load_lines(fy):
    return (ROOT / FILES[fy]).read_text(encoding="utf-8", errors="replace").split("\n")

def find_title(lines, pat):
    for i, l in enumerate(lines, 1):
        if l.startswith("<TITLE") and re.search(pat, l):
            return i
    return None

def num(t):
    t = t.replace(",", "").strip()
    if t in ("", "-"):
        return None
    neg = t.startswith("(") and t.endswith(")") or t.startswith("-") or t.startswith("△")
    t = t.strip("()-△ ")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v

def read_statement(fy, title_pat=r"4-2\. 포괄손익계산서"):
    """-> (title_line, end_line, rows) rows = list of dict(label, tr_line, cells=[dict(acode, ctx, text, val, line)])"""
    lines = load_lines(fy)
    s = find_title(lines, title_pat)
    # section ends at next <TITLE
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
            # value P is on the next non-empty lines until </TE>
            j, txt, pline = i + 1, [], None
            inline = re.search(r">([^<]*)</T[EH]>\s*$", l)
            if inline:                      # single-line cell: <TE ...>text</TE>
                txt.append(inline.group(1).replace("　", " ").strip())
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

def short_ctx(c):
    m = re.match(r"([CP]FY\d{4}d[A-Z]+)_", c)
    sep = "SEP" if "SeparateMember" in c else ("CON" if "ConsolidatedMember" in c else "---")
    return (m.group(1) if m else c[:20]) + ":" + sep
