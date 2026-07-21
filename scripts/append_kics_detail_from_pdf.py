# -*- coding: utf-8 -*-
"""Append the [경과조치 적용 전 지급여력비율 세부] table to md_inbox MDs by
extracting it directly from the PDF text layer with pdfplumber.

Why: for some 2026.1Q PDFs (삼성화재/악사/DB생명/농협생명/하나손해) docling drops
the K-ICS detail pages even at --max-hit-pages 40, although the pages have a
normal text layer. Rather than fighting docling, rebuild just that table from
the PDF and append it under the canonical section heading so the standard fill
pipeline (extract_kics_detail_rows section path) consumes it unchanged.

- Merged cells (multiple logical rows in one physical row) are exploded using
  the preserved in-cell newlines: label lines are grouped by row-label start
  patterns and zipped 1:1 with value lines; rows that don't reconcile are
  dropped whole.
- Amounts are rescaled to 억원 when the page unit says 백만원/천원 (ratio rows
  containing 비율 are kept as-is). The appended block always states 억원.
- Idempotent: re-running replaces the previously appended block (marker line).
- NOTE: a docling re-conversion overwrites the md_inbox MD — re-run this script
  afterwards.

Usage:
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
      scripts/append_kics_detail_from_pdf.py FY2026_Q1 KR0008 KR0049 ...
"""
from __future__ import annotations

import glob
import logging
import re
import sys
import warnings
from pathlib import Path

import pdfplumber

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
MARKER = "<!-- kics-detail appended from pdf text layer by append_kics_detail_from_pdf.py -->"
HEADING = "## [경과조치 적용 전 지급여력비율 세부]"

_LABEL_START = re.compile(
    r"^(가|나|다)\.|^[ⅠⅡⅢⅣⅤ]|^\d+\.|^[-–]\s|^\(분산"
    r"|^기본자본|^보완자본|^지급여력|^생명|^일반손해|^시장위험|^신용위험"
    r"|^운영위험|^법인세|^기타요구|^분산효과"
)
_NUM_LINE = re.compile(r"^-?[\d,]+(?:\.\d+)?$")


def _explode(row: list[str | None]) -> list[tuple[str, list[str]]]:
    """One physical row -> list of (label, [v1, v2, ...]) logical rows."""
    label_cell = (row[0] or "").strip()
    value_cells = [(c or "").strip() for c in row[1:]]
    if not label_cell:
        return []
    label_lines = [l.strip() for l in label_cell.split("\n") if l.strip()]
    labels: list[str] = []
    for line in label_lines:
        if labels and not _LABEL_START.match(line):
            labels[-1] += " " + line
        else:
            labels.append(line)
    value_rows = [[v.strip() for v in c.split("\n") if v.strip()] for c in value_cells]
    n = len(labels)
    if n == 1:
        return [(labels[0], [" ".join(vr) if vr else "" for vr in value_rows])]
    # merged: every value column must split into exactly n numeric lines
    for vr in value_rows:
        if vr and len(vr) != n:
            return []
        if any(v != "-" and not _NUM_LINE.match(v) for v in vr):
            return []
    out = []
    for i in range(n):
        out.append((labels[i], [vr[i] if vr else "" for vr in value_rows]))
    return out


def _scale_value(v: str, scale: float) -> str:
    if not v or v == "-" or scale == 1.0 or not _NUM_LINE.match(v):
        return v
    num = float(v.replace(",", ""))
    s = num / scale
    if abs(s - round(s)) < 1e-6:
        return f"{int(round(s)):,}"
    return f"{s:,.2f}"


def _detail_pages(pdf: pdfplumber.PDF) -> list[int]:
    """Start page = the one whose text carries the [세부] heading; extend while
    the cumulative text hasn't reached the 다. 지급여력비율 closing row (max 3)."""
    start = None
    for i, page in enumerate(pdf.pages):
        t = (page.extract_text() or "").replace(" ", "")
        if "경과조치적용전" in t and "지급여력비율세부" in t:
            start = i
            break
    if start is None:
        return []
    pages = [start]
    acc = (pdf.pages[start].extract_text() or "").replace(" ", "")
    while "다.지급여력비율" not in acc and len(pages) < 3 and pages[-1] + 1 < len(pdf.pages):
        nxt = pages[-1] + 1
        pages.append(nxt)
        acc += (pdf.pages[nxt].extract_text() or "").replace(" ", "")
    return pages


def _page_scale(text: str) -> float:
    """Unit of the [세부] table: the (단위: …) marker between the heading and
    the table body on the start page."""
    compact = text.replace(" ", "")
    pos = compact.find("지급여력비율세부")
    window = compact[pos : pos + 120] if pos >= 0 else compact[:200]
    if "백만원" in window:
        return 100.0
    if "천원" in window:
        return 100_000.0
    return 1.0


def extract_detail_table(pdf_path: Path) -> list[list[str]] | None:
    with pdfplumber.open(pdf_path) as pdf:
        pages = _detail_pages(pdf)
        if not pages:
            return None
        scale = _page_scale(pdf.pages[pages[0]].extract_text() or "")
        out: list[list[str]] = []
        header_done = False
        for pi in pages:
            for tbl in pdf.pages[pi].extract_tables():
                if not tbl:
                    continue
                head = "".join(c or "" for c in tbl[0]).replace(" ", "")
                body = tbl
                if "구분" in head and ("분기" in head or "당분기" in head or "결산" in head):
                    if not header_done:
                        out.append([(c or "").replace("\n", " ").strip() for c in tbl[0]])
                        header_done = True
                    body = tbl[1:]
                elif not out:
                    continue  # before header: unrelated table
                joined = "".join((r[0] or "") for r in body).replace(" ", "")
                if pi == pages[0] and "지급여력금액" not in joined:
                    continue  # start page: must be the detail table itself
                for row in body:
                    for label, vals in _explode(row):
                        if "비율" in label.replace(" ", ""):
                            out.append([label] + vals)
                        else:
                            out.append([label] + [_scale_value(v, scale) for v in vals])
            if header_done and out and "다." in "".join(r[0] for r in out):
                break
        return out if header_done and len(out) > 4 else None


def extract_prepost_table(pdf_path: Path) -> tuple[list[list[str]], float] | None:
    """2nd-chance source when the [세부] table has no text layer (e.g. 악사
    2026.1Q p16 is a full-page image): the 공통적용 경과조치 pre/post table.
    Returns (rows, scale) — rows kept in source units; the appended block
    carries the original (단위: …) line and the parser-side pre/post fallback
    rescales on read."""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = (page.extract_text() or "").replace(" ", "")
            if "경과조치적용전" not in text or "지급여력기준금액" not in text:
                continue
            scale = 100.0 if "백만원" in text else (100_000.0 if "천원" in text else 1.0)
            for tbl in page.extract_tables():
                if not tbl or len(tbl) < 4:
                    continue
                head = "".join(c or "" for c in tbl[0]).replace(" ", "")
                if "경과조치적용전" not in head:
                    continue
                joined = "".join((r[0] or "") for r in tbl).replace(" ", "")
                if "지급여력금액" not in joined or "지급여력기준금액" not in joined:
                    continue
                rows = [
                    [(c or "").replace("\n", " ").strip() for c in r] for r in tbl
                ]
                return rows, scale
    return None


def serialise_md(table: list[list[str]]) -> str:
    width = max(len(r) for r in table)
    lines = []
    for i, row in enumerate(table):
        cells = row + [""] * (width - len(row))
        lines.append("| " + " | ".join(cells) + " |")
        if i == 0:
            lines.append("|" + "---|" * width)
    return "\n".join(lines)


def append_to_md(md_path: Path, table_md: str) -> None:
    content = md_path.read_text(encoding="utf-8")
    if MARKER in content:
        content = content.split(MARKER)[0].rstrip() + "\n"
    block = f"\n{MARKER}\n\n{HEADING}\n\n(단위: 억원, %)\n\n{table_md}\n"
    md_path.write_text(content.rstrip() + "\n" + block, encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: append_kics_detail_from_pdf.py <PERIOD> <KRcode> [...]")
        return 1
    period = sys.argv[1]
    codes = sys.argv[2:]
    raw = REPO / "data" / "disclosure" / period / "raw"
    inbox = REPO / "md_inbox" / period
    n_ok = 0
    for code in codes:
        pdfs = sorted(raw.glob(f"{code}_*.pdf"))
        mds = sorted(inbox.glob(f"{code}_*.md"))
        if not pdfs or not mds:
            print(f"{code}: missing pdf or md (pdf={len(pdfs)}, md={len(mds)})")
            continue
        table = extract_detail_table(pdfs[0])
        if table:
            append_to_md(mds[0], serialise_md(table))
            print(f"{code}: appended {len(table) - 1} detail rows -> {mds[0].name}")
            n_ok += 1
            continue
        pp = extract_prepost_table(pdfs[0])
        if not pp:
            print(f"{code}: no detail/pre-post table in text layer")
            continue
        rows, scale = pp
        unit = "백만원" if scale == 100.0 else ("천원" if scale == 100_000.0 else "억원")
        content = mds[0].read_text(encoding="utf-8")
        if MARKER in content:
            content = content.split(MARKER)[0].rstrip() + "\n"
        block = (
            f"\n{MARKER}\n\n## [지급여력비율의 경과조치 적용에 관한 사항]\n\n"
            f"(단위: {unit}, %)\n\n{serialise_md(rows)}\n"
        )
        mds[0].write_text(content.rstrip() + "\n" + block, encoding="utf-8")
        print(f"{code}: appended {len(rows) - 1} pre/post rows ({unit}) -> {mds[0].name}")
        n_ok += 1
    print(f"{n_ok}/{len(codes)} ok")
    return 0 if n_ok == len(codes) else 2


if __name__ == "__main__":
    main()
    sys.exit()
