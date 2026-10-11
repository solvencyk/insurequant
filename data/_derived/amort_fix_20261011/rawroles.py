# -*- coding: utf-8 -*-
"""Helpers shared by the a0x probes (ticket 20261011T1900Z, CSM amortisation schedule picks the prior-year table).

raw_role(lines, line_no): the reference-date role of a <TABLE> in a DART XML, read from what introduces it.
  - `line_no` is the 1-based line of the `<TABLE` start in the raw file split on '\n' (same convention as src/ifrs17 extractors).
  - walk upwards from the table. Three layouts exist in the FY2025 filings:
      (A) a paragraph        <P>...다음과 같습니다(단위:천원).<당기말></P>  /  a bare  <P><전기말></P>      (라이나 · 동양 · AIA · 메리츠 ...)
      (B) a one-row mini-table <TABLE><TR><TD><당기말></TD><TD>(단위: 백만원)</TD></TR></TABLE>           (DB손해 · 삼성 · 흥국 ...)
      (C) a plain-text marker paragraph with other wording ("당기말" "전기말" alone, "제NN(당)기" ...)
    a table that is itself a data table (more than 6 cells or no marker) is jumped over (so the right half of a split table
    inherits the marker of its left half); the first <P> paragraph that carries text but no marker ends the walk (role None).
  Returns (role, line, text) with role in {"cur", "prior", None}.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

_TAGS = re.compile(r"<[^<>]*>")
_TD = re.compile(r"<TD\b[^>]*>(.*?)</TD>", re.S)
_MARK_ANGLE = re.compile(r"[<\(\[](당기말|전기말|당기|전기|당반기말|전반기말|당반기|전반기|당분기말|전분기말|당분기|전분기)[>\)\]]")
_MARK_BARE = re.compile(r"^\s*[-•·]?\s*(당기말|전기말|당기|전기)\s*$")
_CUR = {"당기말", "당기", "당반기말", "당반기", "당분기말", "당분기"}


def role_of_text(txt: str):
    m = _MARK_ANGLE.findall(txt)
    if m:
        w = m[-1]
        return ("cur" if w in _CUR else "prior"), w
    mb = _MARK_BARE.match(txt)
    if mb:
        w = mb.group(1)
        return ("cur" if w in _CUR else "prior"), w
    return None, None


def _para_text(line: str) -> str:
    s = line.strip()
    return s[3:-4] if (s.startswith("<P>") and s.endswith("</P>")) else ""


def _mini_table_role(chunk: str):
    """role of a small table whose cells carry the marker (layout B); None for a data table"""
    cells = [c.strip() for c in _TD.findall(chunk)]
    if not cells or len(cells) > 6:
        return None, None
    for c in cells:
        role, w = role_of_text(c)
        if role:
            return role, c
    return None, None


def raw_role(lines: list[str], line_no: int):
    i = line_no - 2           # 0-based index of the line just above the `<TABLE`
    while i >= 0:
        s = lines[i].strip()
        if not s or s.startswith("<PGBRK"):
            i -= 1
            continue
        if s.startswith("</TABLE"):
            end = i
            depth = 1
            i -= 1
            while i >= 0 and depth:
                t = lines[i].strip()
                if t.startswith("</TABLE"):
                    depth += 1
                elif t.startswith("<TABLE"):
                    depth -= 1
                i -= 1
            start = i + 1                      # line index of the matching <TABLE
            role, cell = _mini_table_role("\n".join(lines[start:end + 1]))
            if role:
                return role, start + 1, "[mini-table] " + cell[:120]
            continue                           # a data table: jump over it
        if s.startswith("<P>"):
            txt = _para_text(lines[i])
            if txt.strip():
                role, word = role_of_text(txt)
                return role, i + 1, txt[:140]
            i -= 1                             # an empty <P></P>: keep walking
            continue
        return None, i + 1, s[:140]
    return None, None, None


# --- far search: the nearest marker ANYWHERE above the table (section headers like "<전기말>1) 계리적 가정",
#     "2) 제75(전)기 기말", "1) 제76(당)기", a SPAN inside a <P>, a mini-table cell) ----------------------------
_MARK_FISCAL = re.compile(r"제\s*\d+\s*\(\s*(당|전)\s*\)\s*기")
_MARK_SHORT = re.compile(r"\(\s*(당|전)\s*\)\s*기")
_ANY_MARK_LINE = re.compile(r"<당기말>|<전기말>|<당기>|<전기>|\(당기말\)|\(전기말\)|\(당기\)|\(전기\)|제\s*\d+\s*\(\s*[당전]\s*\)\s*기|\(\s*[당전]\s*\)\s*기")


def _line_role(s: str):
    """role of ONE raw line that carries a marker (explicit marker forms only; a sentence that merely mentions both
    periods, e.g. '당기와 전기 중 ...다음과 같습니다.', is not a marker)."""
    m = _MARK_ANGLE.findall(s)
    if m:
        w = m[-1]
        return ("cur" if w in _CUR else "prior"), w
    m = _MARK_FISCAL.search(s) or _MARK_SHORT.search(s)
    if m:
        return ("cur" if m.group(1) == "당" else "prior"), m.group(0)
    return None, None


def far_role(lines: list[str], line_no: int, max_up: int = 4000):
    """(role, distance_in_lines, text) of the nearest explicit period marker above the table, or (None, None, None)."""
    lo = max(0, line_no - 2 - max_up)
    for i in range(line_no - 2, lo - 1, -1):
        s = lines[i]
        if not _ANY_MARK_LINE.search(s):
            continue
        t = s.strip()
        if not (t.startswith("<P") or t.startswith("<SPAN") or t.startswith("<TD") or t.startswith("<TITLE") or "<P" in t or "<SPAN" in t):
            continue
        role, w = _line_role(t)
        if role:
            return role, (line_no - 1 - i), re.sub(r"\s+", " ", t)[:120]
    return None, None, None


_RAW_CACHE: dict[str, list[str] | None] = {}


def raw_lines_for(rcept: str, source_xml: str):
    """lines of the raw XML for a (rcept, `_source_xml`) pair, or None when the raw file is not on this disk."""
    key = f"{rcept}/{source_xml}"
    if key in _RAW_CACHE:
        return _RAW_CACHE[key]
    found = None
    for d in ROOT.glob(f"data/dart/FY*/raw/*_{rcept}"):
        p = d / source_xml
        if p.is_file():
            found = p
            break
    lines = None if found is None else found.read_text(encoding="utf-8").split("\n")
    _RAW_CACHE[key] = lines
    return lines
