# -*- coding: utf-8 -*-
"""
Quarterly 경영공시 PDF (2025.1Q-2026.2Q template)  2-4 "회계모형별, 포트폴리오별 보험부채 현황"  ->  the prior-year-same-quarter table.

The quarterly template prints the table for the quarter itself ('<2025년 1분기>' / '해당 분기(25.1Q)') and, for many filers, a
second table for the same quarter one year earlier ('<2024년 1분기>' / '전년 동기(24.1Q)') right behind it.  That second table is the
ONLY disclosure of the 2024.1Q-3Q balances in this form (the 2024 quarterly 경영공시 had no such table) -- the ticket of the
interim-quarter round (2026-10-11).  scripts/extract_insurance_liability_model_pdf.py reads the year-end template; this module reads
the quarterly one with the same run-length rule (7 = GMM BEL/RA/CSM + VFA BEL/RA/CSM + PAA, 6 = no PAA, 4 = GMM BEL/RA/CSM + PAA,
3 = GMM only, 1 = PAA only, 8 = one stray leading token), reusing its number reader.  Additive module: nothing existing is changed.

What it does that the year-end reader does not:
  * the section start is a page that carries the header AND a 단위 marker (a 목차 line is skipped);
  * the section is cut at the next section header (2-5 / Ⅲ), so a later 합계 row (3-2 유가증권) is never read as a table;
  * every table gets the label text found in front of it ('<2024년 1분기>', '전년 동기(24.1Q)', ...) and the label kind cur / prior.

Pure reader: no master is read or written.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_model_pdf as M  # noqa: E402
import extract_insurance_liability_portfolio as S1  # noqa: E402

# label forms of the two tables of the quarterly template
RE_LABEL_ANGLE = re.compile(r"[<\[【《]\s*(20\d\d)\s*년?\s*(?:([1-4])\s*분?\s*기?)?\s*[>\]】》]")   # <2025년 1분기>, <2025 년 1 분기>, 【2024년 1분기】
RE_LABEL_PAREN = re.compile(r"\(\s*(\d\d)\s*\.\s*([1-4])\s*Q\s*\)")                            # 해당 분기(25.1Q), 전년 동기(24.1Q)
RE_LABEL_WORD_CUR = re.compile(r"해당\s*분기|당\s*분기|당\s*반기|당\s*기\s*[\(<]")
RE_LABEL_WORD_PRIOR = re.compile(r"전년\s*동\s*기|전년\s*동\s*분\s*기|전\s*년\s*동\s*기")
# the next section starts with '2-5.' (also character-doubled '22--55..') or the words 무·저해지, or chapter Ⅲ.  The '2-5.' prefix must be inside the cut:
# left behind it reads as the numbers '2' and '-5' after the last 합계 row (현대해상 2025.1Q prior-year table came out as a 6-number run)
RE_NEXT_SECTION = re.compile(r"(?m)^[ \t]*2{1,2}[ \t]*-{1,2}[ \t]*5{1,2}[ \t]*[\.\)]|"
                             + S1.flex_cjk("무") + r"[·∙ㆍ.]{0,2}\s*" + S1.flex_cjk("저해지") + r"|Ⅲ\s*\.\s*자산|3\s*-\s*1\s*\.\s*자산"
                             + r"|4\s*-\s*6\s*-\s*3\s*\)|" + S1.flex_cjk("보험부채") + r"\s*" + S1.flex_cjk("변동내역") + "|" + S1.flex_cjk("계리적") + r"\s*" + S1.flex_cjk("가정"))


RE_TAIL_NUMS = re.compile(r"((?:\s+(?:△?\(?-?\d[\d,]*(?:\.\d+)?\)?|-))+)\s*$")
RE_ONE_NUM = re.compile(r"△?\(?-?\d[\d,]*(?:\.\d+)?\)?|-")


def parse_detail_rows(seg: str):
    """lines of a table segment that END with >= 3 number tokens ('-' = 0) -> [{'label', 'nums'}]; header / note lines never end with numbers"""
    rows = []
    for line in seg.split("\n"):
        s = line.rstrip()
        m = RE_TAIL_NUMS.search(s)
        if not m:
            continue
        toks = RE_ONE_NUM.findall(m.group(1))
        if len(toks) < 3:
            continue
        nums = []
        for t in toks:
            if t == "-":
                nums.append(0.0)
                continue
            neg = t.startswith("△") or t.startswith("(") or t.startswith("-")
            core = t.lstrip("△(-").rstrip(")").replace(",", "")
            try:
                v = float(core)
            except ValueError:
                break
            nums.append(-v if neg else v)
        else:
            rows.append({"label": s[: m.start()].strip()[:40], "nums": nums})
    return rows


def footing(rows, run):
    """compare the 합계 run with the column sums of the detail rows that carry exactly as many tokens as the 합계 row.
    -> {'n_full', 'n_other', 'sums', 'diffs', 'ok'} or None when no row can be placed.  Each row is rounded (+-0.5), so a column may differ by 0.5 x rows + 1."""
    K = len(run)
    full = [r for r in rows if len(r["nums"]) == K]
    if not full:
        return None
    sums = [round(sum(r["nums"][c] for r in full), 4) for c in range(K)]
    diffs = [round(sums[c] - run[c], 4) for c in range(K)]
    tol = 0.5 * len(full) + 1.0
    return {"n_full": len(full), "n_other": len([r for r in rows if len(r["nums"]) != K]), "sums": sums, "diffs": diffs, "tol": tol, "ok": all(abs(d) <= tol for d in diffs)}


def footing_mixed(rows, slots):
    """footing() for tables whose detail rows carry DIFFERENT token counts (뮌헨재보험 prints '일반 0 0 0 -49.09' = GMM zeros + PAA, 4 tokens, in a 7-token table):
    each row is placed into the 7 slots by its OWN length with the stage-1 rule (M.slots), then all rows are summed against the 합계 slots.
    -> {'n_rows', 'sums', 'diffs', 'tol', 'ok'} or None.  tol = 0.5 per row + 1 (every printed row is rounded)."""
    if not slots:
        return None
    sums, n = {i: 0.0 for i in range(1, 8)}, 0
    for r in rows:
        v, _kind = M.slots(r["nums"])
        if not v:
            continue
        n += 1
        for i in range(1, 8):
            sums[i] += v[i]
    if n == 0:
        return None
    diffs = {i: round(sums[i] - slots[i], 4) for i in range(1, 8)}
    tol = 0.5 * n + 1.0
    return {"n_rows": n, "sums": {i: round(sums[i], 4) for i in sums}, "diffs": diffs, "tol": tol, "ok": all(abs(d) <= tol for d in diffs.values())}


def page_texts(pdf_path, last: int = 45):
    """1-indexed {page: text} of pages 1..last by pdfplumber, fitz when pdfplumber cannot open the file; the printed page-number
    line ('- 24 -') is removed as in the year-end reader"""
    import fitz
    import pdfplumber
    out, src = {}, "pdfplumber"
    try:
        pdf = pdfplumber.open(str(pdf_path))
        for p in range(1, min(last, len(pdf.pages)) + 1):
            out[p] = M.FOOTER.sub("", pdf.pages[p - 1].extract_text() or "")
        pdf.close()
    except Exception:  # noqa: BLE001  (Unexpected EOF etc.)
        src = "fitz"
        doc = fitz.open(str(pdf_path))
        for p in range(1, min(last, doc.page_count) + 1):
            out[p] = M.FOOTER.sub("", doc[p - 1].get_text("text"))
        doc.close()
    return out, src


def find_section_start(texts: dict):
    """first page whose text holds the 2-4 header followed by a 단위 marker within 250 characters (the window may spill onto the
    next page); a table-of-contents line has no 단위 marker.  -> page or None"""
    pages = sorted(texts)
    for p in pages:
        t = texts[p]
        for m in S1.RE_HEADER_24.finditer(t):
            window = t[m.start(): m.start() + 250]
            if len(window) < 250 and (p + 1) in texts:
                window += texts[p + 1][: 250 - len(window)]
            if S1.RE_UNIT_MARKER.search(window):
                return p
    return None


def label_of(seg: str):
    """(kind, year, quarter, text) of the table label found in the text segment in front of a 합계 row.  kind cur | prior | None.
    The LAST label wins (a segment can hold the previous table's trailing furniture)."""
    best = None
    for m in RE_LABEL_ANGLE.finditer(seg):
        best = (m.start(), None, int(m.group(1)), (int(m.group(2)) if m.group(2) else None), m.group(0))
    for m in RE_LABEL_PAREN.finditer(seg):
        if best is None or m.start() > best[0]:
            best = (m.start(), None, 2000 + int(m.group(1)), int(m.group(2)), m.group(0))
    for m in RE_LABEL_WORD_PRIOR.finditer(seg):
        if best is None or m.start() > best[0]:
            best = (m.start(), "prior", None, None, m.group(0))
    for m in RE_LABEL_WORD_CUR.finditer(seg):
        if best is None or m.start() > best[0]:
            best = (m.start(), "cur", None, None, m.group(0))
    if best is None:
        return None, None, None, None
    return best[1], best[2], best[3], best[4]


def read_interim(pdf_path, max_pages: int = 45, lookahead: int = 4):
    """-> {'source', 'start', 'unit', 'unit_div', 'tables':[{'page','label','label_kind','label_year','label_quarter','run','slots','kind'}],
    'status'}.  status: ok | scan_or_no_header (no header page in the text layer)"""
    texts, src = page_texts(pdf_path, max_pages)
    start = find_section_start(texts)
    if start is None:
        return {"source": src, "start": None, "unit": None, "unit_div": None, "tables": [], "status": "scan_or_no_header", "n_pages_read": len(texts)}
    blob, spans = "", []
    for p in range(start, min(start + lookahead, max(texts)) + 1):
        spans.append((len(blob), p))
        blob += texts[p] + "\n\f"
    page_of = lambda off: max((pg for o, pg in spans if o <= off), default=start)
    h = S1.RE_HEADER_24.search(blob)
    begin = h.start() if h else 0
    sect = blob[begin:]
    e = RE_NEXT_SECTION.search(sect, 200)
    if e:
        sect = sect[: e.start()]
    unit_div, unit = S1.detect_unit_divisor(sect[:600])
    full_doubling = "((" in sect[:700]
    tables, prev_end = [], 0
    for m in S1.RE_TOTAL_LABEL.finditer(sect):
        seg = sect[prev_end: m.start()]
        run = M.run_after(sect, m.end(), full_doubling)
        if not run:
            continue
        kind_l, yr, qu, text = label_of(re.sub(r"(.)\1", r"\1", seg) if full_doubling else seg)
        v, kind = M.slots(run)
        rows_ = parse_detail_rows(re.sub(r"(.)\1", r"\1", seg) if full_doubling else seg)
        # the first line of a later table's segment is the REST of the previous table's 합계 line (its numbers, first token swallowed by the label regex):
        # it must not be read as a detail row of this table
        first_line, _, rest_seg = seg.partition("\n")
        seg_rows = rest_seg if (prev_end and not re.search(r"[가-힣A-Za-z]", first_line)) else seg
        rows_m = parse_detail_rows(re.sub(r"(.)\1", r"\1", seg_rows) if full_doubling else seg_rows)
        tables.append({"page": page_of(begin + m.start()), "label": text, "label_kind": kind_l, "label_year": yr, "label_quarter": qu,
                       "run": run, "slots": v, "kind": kind, "n_detail_rows": len(rows_), "footing": footing(rows_, run),
                       "footing_mixed": footing_mixed(rows_m, v), "detail_rows": rows_m})
        prev_end = m.end()
    return {"source": src, "start": start, "unit": unit, "unit_div": unit_div, "tables": tables, "status": "ok", "n_pages_read": len(texts)}


if __name__ == "__main__":
    import glob
    sys.stdout.reconfigure(encoding="utf-8")
    fy, codes = sys.argv[1], sys.argv[2:]
    for pdf in sorted(glob.glob(str(REPO / "data" / "disclosure" / fy / "raw" / "KR*.pdf"))):
        code = Path(pdf).name[:6]
        if codes and code not in codes:
            continue
        r = read_interim(pdf)
        print(code, r["status"], "start", r["start"], r["source"], r["unit"],
              [(t["page"], t["label"], t["kind"], len(t["run"]), (None if t.get("footing") is None else ("foot_ok" if t["footing"]["ok"] else "FOOT_BAD")),
                t.get("n_detail_rows")) for t in r["tables"]])
