# -*- coding: utf-8 -*-
"""
Year-end 경영공시 PDF  4-6-2 "회계모형별, 포트폴리오별 보험부채 현황"  ->  insurance_liability_portfolio.json items 1-8.

The year-end (결산) template prints the table for the current year ('<2024년>') and, for most filers, a second table for
the prior year end ('<2023년>') right behind it.  scripts/extract_insurance_liability_portfolio.py (stage 1) reads only the
FIRST 합계 row after the header and cannot read decimals ('72,746.5' -> 72,746; IBK연금); this module reads every 합계 row of the
section, keeps the decimals, ties each row to the year marker in front of it, and maps the numbers to the 7 value slots with
the SAME run-length rule as stage 1 (7 = GMM BEL/RA/CSM + VFA BEL/RA/CSM + PAA, 6 = no PAA, 4 = GMM + PAA, 3 = GMM only,
1 = PAA only, 8 = one stray leading token).  Any other length is NOT guessed (status 'run_length').

Text source: pdfplumber (as stage 1), fitz when pdfplumber cannot open the file (DB손보 'Unexpected EOF').
Pure reader: no master is read or written.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_portfolio as S1  # noqa: E402  (regexes and the stage-1 number reader)

YEAR_MARK = re.compile(r"<\s*(20\d\d)\s*년\s*>|\(\s*(20\d\d)\s*년\s*\)")
SECTION_END = re.compile(S1.flex_cjk("보험부채") + r"\s*" + S1.flex_cjk("변동내역") + "|" + S1.flex_cjk("계리적") + r"\s*" + S1.flex_cjk("가정"))
# a number token: optional sign / parentheses, digits with commas, optional decimals; a lone dash is a blank cell
NUM = re.compile(r"\s*(△?\(?-?\d[\d,]*(?:\.\d+)?\)?|-(?!\d))")
COL_MAP = {7: "full", 6: "no_paa", 4: "gmm_paa", 3: "gmm", 1: "paa_only", 8: "skip_lead"}


FOOTER = re.compile(r"(?m)^[ \t]*-[ \t]*\d{1,3}[ \t]*-[ \t]*$")      # a printed page number line: '- 24 -'


def read_pages(pdf_path, first: int, last: int):
    """text of the 1-indexed pages first..last (clipped) -> {page: text}, source 'pdfplumber' | 'fitz'.
    Printed page-number lines ('- 24 -') are removed: behind a 합계 row they read as the numbers '-', 24, '-'
    (KDB생명 4-6-2 came out as a 10-number run)."""
    import fitz
    import pdfplumber
    out, src = {}, "pdfplumber"
    try:
        pdf = pdfplumber.open(str(pdf_path))
        n = len(pdf.pages)
        for p in range(max(first, 1), min(last, n) + 1):
            out[p] = FOOTER.sub("", pdf.pages[p - 1].extract_text() or "")
        pdf.close()
    except Exception:  # noqa: BLE001  (Unexpected EOF etc.)
        src = "fitz"
        doc = fitz.open(str(pdf_path))
        for p in range(max(first, 1), min(last, doc.page_count) + 1):
            out[p] = FOOTER.sub("", doc[p - 1].get_text("text"))
        doc.close()
    return out, src


def find_start_page(pdf_path, max_pages: int = 80):
    """1-indexed page of the 4-6-2 header ('회계모형별, 포트폴리오별 보험부채 현황') in the 경영공시 body (not the appended
    notes), by fitz text (no scan guard: image-only files return None).  The header words are matched on the
    whitespace-free text, also after collapsing the doubled characters some filers print (한화생명)."""
    import fitz
    doc = fitz.open(str(pdf_path))
    try:
        for i in range(min(doc.page_count, max_pages)):
            t = doc[i].get_text("text") or ""
            tn = re.sub(r"\s+", "", t)
            for cand in (tn, re.sub(r"([^\d,.\s])\1", r"\1", tn)):
                if "회계모형별" in cand and "포트폴리오별" in cand and "보험부채현황" in cand:
                    return i + 1
        return None
    finally:
        doc.close()


def run_after(text: str, pos: int, full_doubling: bool = False):
    """maximal run of number tokens right behind a 합계 label"""
    tail = text[pos:pos + 600].split("\f")[0]        # never run into the next page's footer ('- 31 -')
    if full_doubling:
        tail = re.sub(r"(.)\1", r"\1", tail)
    run, p = [], 0
    while len(run) < 12:
        m = NUM.match(tail, p)
        if not m:
            break
        tok = m.group(1)
        if tok == "-":
            v = 0.0
        else:
            neg = tok.startswith("△") or tok.startswith("(") or tok.startswith("-")
            core = tok.lstrip("△(-").rstrip(")").replace(",", "")
            try:
                v = float(core)
            except ValueError:
                break
            v = -v if neg else v
        run.append(v)
        p = m.end()
    return run


def slots(run: list):
    """run -> {1..7: value} by the stage-1 length rule, or None"""
    L = len(run)
    kind = COL_MAP.get(L)
    if kind is None:
        return None, f"run_length_{L}"
    if kind == "skip_lead":
        run, kind = run[1:], "full"
    if kind == "paa_only":
        return {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: run[0]}, kind
    v = {1: run[0], 2: run[1], 3: run[2]}
    if kind == "full":
        v.update({4: run[3], 5: run[4], 6: run[5], 7: run[6]})
    elif kind == "no_paa":
        v.update({4: run[3], 5: run[4], 6: run[5], 7: 0.0})
    elif kind == "gmm_paa":
        v.update({4: 0.0, 5: 0.0, 6: 0.0, 7: run[3]})
    else:                                       # gmm only
        v.update({4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0})
    return v, kind


def read_tables(pdf_path, start_page: int, lookahead: int = 4):
    """-> {'source': pdfplumber|fitz, 'unit': '억원'..., 'tables': [{'year': 2024|2023|None, 'page': p, 'run': [...],
    'slots': {1..7}|None, 'kind': str, 'unit_div': float}], 'blob_len': n}"""
    texts, src = read_pages(pdf_path, start_page - 1, start_page + lookahead)
    blob = ""
    spans = []                                   # (offset, page)
    for p in sorted(texts):
        spans.append((len(blob), p))
        blob += texts[p] + "\n\f"
    page_of = lambda off: max((pg for o, pg in spans if o <= off), default=start_page)
    h = S1.RE_HEADER_24.search(blob)
    begin = h.start() if h else 0
    sect = blob[begin:]
    # fitz lists a table's cells AFTER the headings that follow it on the page (DB손보: '4-6-3) 보험부채 변동내역' comes before the
    # 4-6-2 numbers), so the section end can only be used on pdfplumber text; a fitz reading keeps the first table only
    e = SECTION_END.search(sect, 200) if src == "pdfplumber" else None
    if e:
        sect = sect[:e.start()]
    unit_div, unit = S1.detect_unit_divisor(sect[:600])
    full_doubling = "((" in sect[:700]
    marks = [(m.start(), int(m.group(1) or m.group(2))) for m in YEAR_MARK.finditer(sect)]
    tables = []
    for m in S1.RE_TOTAL_LABEL.finditer(sect):
        run = run_after(sect, m.end(), full_doubling)
        if not run:
            continue
        yr = None
        for off, y in marks:
            if off <= m.start():
                yr = y
        v, kind = slots(run)
        tables.append({"year": yr, "page": page_of(begin + m.start()), "run": run, "slots": v, "kind": kind,
                       "unit_div": unit_div, "unit": unit})
    if src == "fitz":
        tables = tables[:1]
    return {"source": src, "unit": unit, "unit_div": unit_div, "tables": tables, "blob_len": len(sect),
            "marks": [y for _, y in marks]}


def eok(slots_: dict, unit_div: float) -> dict:
    return {k: round(v / unit_div, 4) for k, v in slots_.items()}
