# -*- coding: utf-8 -*-
"""Geometry-based table row reconstruction for management-disclosure PDFs (PyMuPDF text layer).

Why not `page.find_tables()` / plain `get_text()`: in these PDFs a table cell frequently holds several
stacked lines (find_tables merges a whole column group into one cell) or the label column and the value
columns are emitted as separate blocks (K-IFRS style statements in won).  Visual rows are therefore rebuilt
from word coordinates: numeric tokens are clustered by their vertical centre, label words are attached to
the nearest numeric row.  Wrapped labels (a label that needs two lines while its numbers sit between the
lines) are handled by attaching every label line to the nearest numeric row within 0.75 row pitches.
Vertical group captions ("자 산", "부 채", ...) sit in a column left of the label column and are dropped by
geometry.  Percentage tokens ("39.40%") are separated from the value columns.

Pure functions, no side effects, stdlib + fitz only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF

_PCT_RE = re.compile(r"^[△▲\-–]?\d[\d,]*(\.\d+)?[%％]$")
_DASH = {"-", "－", "–", "—", "‐", "−"}
_SIGN_TOKENS = {"-", "－", "–", "‐", "−", "△", "▲", "("}


_NOTE_LIST_RE = re.compile(r"^\d{1,3}(,\d{1,2})+$")


def parse_num(tok: str):
    """'1,234' -> 1234.0 ; '△12' -> -12.0 ; '(12)' -> -12.0 ; '-12' -> -12.0 ; else None (bare dash -> None)."""
    t = tok.strip().replace("　", "")
    if not t:
        return None
    neg = False
    m = re.fullmatch(r"\(\s*[-–△▲]\s*\)\s*(\d[\d,]*(?:\.\d+)?)", t)
    if m:                                         # '(-)4,000' / '(△)4,000'
        neg, t = True, m.group(1)
    elif t[0] in "△▲":
        neg, t = True, t[1:]
    elif t.startswith("(") and t.endswith(")"):
        neg, t = True, t[1:-1]
    elif t[0] in "-–" and len(t) > 1:
        neg, t = True, t[1:]
    if _NOTE_LIST_RE.match(t):
        return None              # '4,7,14' / '5,7' (note-reference lists) are not amounts
    t = t.replace(",", "")
    if not t or not re.fullmatch(r"\d+(\.\d+)?", t):
        return None
    v = float(t)
    return -v if neg else v


def is_note_list(tok: str) -> bool:
    """'4,7,14', '5,7', '11,14': a cell of note references ('주석'), never a label or an amount.  Every comma group after
    the first has 1-2 digits (a thousands separator is always followed by exactly 3)."""
    return _NOTE_LIST_RE.match(tok.strip()) is not None


def is_dash(tok: str) -> bool:
    return tok.strip() in _DASH


def is_pct(tok: str) -> bool:
    return _PCT_RE.match(tok.strip()) is not None


def is_numeric_token(tok: str) -> bool:
    return parse_num(tok) is not None


def dedupe_doubled(s: str) -> str:
    """'현현금금및및예예치치금금' -> '현금및예치금' (bold simulated by overprinting)."""
    t = "".join(s.split())
    if len(t) >= 4 and len(t) % 2 == 0 and t[0::2] == t[1::2]:
        return t[0::2]
    return s


@dataclass
class Row:
    label: str                 # label with all whitespace removed
    label_raw: str             # label with single spaces
    vals: list                 # numeric values (floats) in x order; dash tokens appear as 0.0 with flag
    dash: list                 # parallel list: True if the token was a bare dash
    xs: list                   # x1 (right edge) of each numeric token
    y: float                   # vertical centre of the numeric row
    page: int = 0
    pcts: list = field(default_factory=list)
    toks: list = field(default_factory=list)


_REP_RE = re.compile(r"(.{2,}?)\1")
_REP1_RE = re.compile(r"(.)\1")


def undouble_label(s: str) -> str:
    """'부채부채및및자본자본총계총계' -> '부채및자본총계' (overprinted text merged into one string).
    Only applied on pages where exact duplicate words were detected."""
    t = "".join(s.split())
    t = _REP_RE.sub(r"\1", t)
    t = _REP1_RE.sub(r"\1", t)
    return t


def _words(page: fitz.Page):
    """(x0, y0, x1, y1, text, yc) with exact duplicate words (same text and box: overprinted text) removed.
    Returns (words, doubled_flag)."""
    ws = page.get_text("words")
    out = []
    seen = set()
    dup = 0
    for x0, y0, x1, y1, t, b, ln, wn in ws:
        t = t.strip()
        if not t:
            continue
        key = (t, round(x0, 0), round(y0, 0), round(x1, 0))
        if key in seen:
            dup += 1
            continue
        seen.add(key)
        out.append((x0, y0, x1, y1, t, (y0 + y1) / 2.0))
    doubled = len(ws) > 20 and dup >= 0.3 * len(ws) * 0.5
    return _merge_signs(_merge_split_thousands(out)), doubled


_SPLIT_HEAD_RE = re.compile(r"^[△▲\-(]?\d{1,3}(,\d{3})*,$")


def _merge_split_thousands(ws):
    """A number whose text layer breaks right after the thousands separator ('1,' + '001', KR0080 2026.2Q p6 prints
    '1, 001' = 1,001) is merged into one token.  Only a head that ends with a comma followed by a token of EXACTLY three
    digits, on the same line and <= 4pt apart, so note-reference lists ('4, 22', '5, 6, 7, 38') are never touched."""
    ws = sorted(ws, key=lambda w: (round(w[5] / 2.6), w[0]))
    out = []
    i = 0
    while i < len(ws):
        w = ws[i]
        if i + 1 < len(ws) and _SPLIT_HEAD_RE.match(w[4]):
            n = ws[i + 1]
            if re.fullmatch(r"\d{3}", n[4]) and abs(n[5] - w[5]) <= 2.6 and 0.0 <= n[0] - w[2] <= 4.0:
                out.append((w[0], min(w[1], n[1]), n[2], max(w[3], n[3]), w[4] + n[4], (w[5] + n[5]) / 2.0))
                i += 2
                continue
        out.append(w)
        i += 1
    return out


def _merge_signs(ws):
    """A minus / triangle / opening parenthesis printed as a separate word right before a number ('- 1,141',
    '△ 1,141') is merged into a negative number.  A genuine nil dash sits in its own column (>= 50pt away), so only
    gaps <= 10pt on the same line are merged."""
    ws = sorted(ws, key=lambda w: (round(w[5] / 2.6), w[0]))
    out = []
    i = 0
    while i < len(ws):
        w = ws[i]
        if w[4] in _SIGN_TOKENS and i + 1 < len(ws):
            n = ws[i + 1]
            v = parse_num(n[4])
            if (abs(n[5] - w[5]) <= 2.6 and 0.0 <= n[0] - w[2] <= 10.0 and v is not None and v >= 0
                    and n[4][0] not in "-–△▲("):
                out.append((w[0], min(w[1], n[1]), n[2], max(w[3], n[3]), "△" + n[4], (w[5] + n[5]) / 2.0))
                i += 2
                continue
        out.append(w)
        i += 1
    return out


def rows_from_page(page: fitz.Page, y_tol: float = 2.6, pageno: int = 0, bbox=None):
    """Reconstruct visual rows.  Returns (rows, free_text_lines) where free_text_lines are text lines that
    could not be attached to a numeric row (section headers, titles, notes): [(y, x0, text)].

    bbox: optional (x0, y0, x1, y1) crop in page points (use to separate stacked tables)."""
    ws, doubled = _words(page)
    if bbox:
        bx0, by0, bx1, by1 = bbox
        ws = [w for w in ws if w[0] >= bx0 - 1 and w[2] <= bx1 + 1 and w[5] >= by0 and w[5] <= by1]
    pct_ws = [w for w in ws if is_pct(w[4])]
    ws = [w for w in ws if not is_pct(w[4]) and not is_note_list(w[4])]
    num_ws = [w for w in ws if (is_numeric_token(w[4]) or is_dash(w[4]))]
    num_ids = {id(w) for w in num_ws}
    txt_ws = [w for w in ws if id(w) not in num_ids]
    if not num_ws:
        return [], [(w[5], w[0], w[4]) for w in txt_ws]

    # cluster numeric words by y centre
    num_ws.sort(key=lambda w: (w[5], w[0]))
    clusters: list[list] = []
    for w in num_ws:
        if clusters and abs(w[5] - sum(x[5] for x in clusters[-1]) / len(clusters[-1])) <= y_tol:
            clusters[-1].append(w)
        else:
            clusters.append([w])
    ys = [sum(x[5] for x in c) / len(c) for c in clusters]
    gaps = sorted(b - a for a, b in zip(ys, ys[1:]) if b - a > 3.0)
    pitch = gaps[len(gaps) // 2] if gaps else 14.0
    # group label words into visual lines by y
    txt_ws.sort(key=lambda w: (w[5], w[0]))
    lines: list[list] = []
    for w in txt_ws:
        if lines and abs(w[5] - lines[-1][0][5]) <= y_tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    row_label_lines: list[list] = [[] for _ in clusters]
    free: list = []
    first_x0 = [min(w[0] for w in c) for c in clusters]
    for ln in lines:
        ly = sum(w[5] for w in ln) / len(ln)
        j = min(range(len(ys)), key=lambda k: abs(ys[k] - ly))
        d = abs(ys[j] - ly)
        lx0 = min(w[0] for w in ln)
        lx1 = max(w[2] for w in ln)
        if d <= max(y_tol, 0.75 * pitch) and lx1 <= first_x0[j] + 3.0:
            row_label_lines[j].append((ly, lx0, lx1, ln))
        else:
            free.append((ly, lx0, " ".join(w[4] for w in sorted(ln, key=lambda w: w[0]))))
    # label column left edge: median x0 of lines with >= 4 characters.  Pages often stack two tables whose label columns
    # start at different x (KR1107 2024.2Q: asset-quality table + equity table), so the edge is taken from the rows
    # NEAR the row (+-6), falling back to the whole page.
    def _long_x0(rows_idx):
        return sorted(l[1] for k in rows_idx for l in row_label_lines[k] if sum(len(w[4]) for w in l[3]) >= 4)
    lx = _long_x0(range(len(clusters)))
    label_left_page = lx[len(lx) // 2] if lx else None
    rows: list[Row] = []
    for j, c in enumerate(clusters):
        c.sort(key=lambda w: w[0])
        vals = [parse_num(w[4]) if not is_dash(w[4]) else 0.0 for w in c]
        dashes = [is_dash(w[4]) for w in c]
        ll = sorted(row_label_lines[j], key=lambda t: t[0])
        near = _long_x0(range(max(0, j - 6), min(len(clusters), j + 7)))
        label_left = near[len(near) // 2] if near else label_left_page
        toks = []
        for ly, lx0, lx1, ln in ll:
            nchar = sum(len(w[4]) for w in ln)
            # vertical group captions sit wholly left of the label column
            if label_left is not None and lx1 < label_left - 2.0 and nchar <= 3:
                continue
            toks.append((ly, lx0, " ".join(w[4] for w in sorted(ln, key=lambda w: w[0]))))
        label_raw = dedupe_doubled(" ".join(t[2] for t in toks))
        if doubled:
            label_raw = undouble_label(label_raw)
        pcts = [w[4] for w in pct_ws if abs(w[5] - ys[j]) <= y_tol]
        rows.append(Row(label="".join(label_raw.split()), label_raw=label_raw, vals=vals, dash=dashes,
                        xs=[w[2] for w in c], y=ys[j], page=pageno, pcts=pcts, toks=toks))
    return rows, free
