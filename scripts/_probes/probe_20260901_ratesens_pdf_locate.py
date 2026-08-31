"""For the 28 companies missing 2026.2Q 금리민감도 rows: search the raw PDF text layer
for the '금리 민감도' / '위험 민감도' section, report which page(s) it's on, total page
count, and whether that page is inside the MD's source_page_ranges window (docling
window-drop diagnosis, same class as 20260831T0700Z ticket but for a different section).

Read-only. Usage: PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
       scripts/_probes/probe_20260901_ratesens_pdf_locate.py
"""
from __future__ import annotations
import io
import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF_DIR = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf"
MD_DIR = REPO / "md_inbox" / "FY2026_Q2"

MISSING = """KR0001 KR0003 KR0004 KR0009 KR0011 KR0029 KR0032 KR0051 KR0068 KR0069
KR0070 KR0071 KR0072 KR0073 KR0079 KR0080 KR0082 KR0083 KR0087 KR0094
KR0097 KR0099 KR0100 KR0104 KR0150 KR1010 KR1011 KR1098""".split()


def norm(s):
    return re.sub(r"\s+", "", s or "")


def parse_ranges(spec: str):
    """'4-50' or '4-19;22-29' -> list of (lo,hi) ints, 1-indexed inclusive."""
    out = []
    if not spec:
        return out
    for part in spec.split(";"):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-")
            out.append((int(lo), int(hi)))
        elif part:
            out.append((int(part), int(part)))
    return out


def in_ranges(page1, ranges):
    return any(lo <= page1 <= hi for lo, hi in ranges)


def frontmatter_field(md_text, key):
    m = re.search(rf'^{key}:\s*"?([^"\n]*)"?\s*$', md_text, re.MULTILINE)
    return m.group(1) if m else None


results = {}
for code in MISSING:
    pdf_hits = sorted(PDF_DIR.glob(f"{code}_*.pdf"))
    md_hits = sorted(MD_DIR.glob(f"{code}_*.md"))
    if not pdf_hits:
        results[code] = {"error": "no pdf"}
        continue
    pdf_path = pdf_hits[0]
    md_text = md_hits[0].read_text(encoding="utf-8") if md_hits else ""
    src_ranges_spec = frontmatter_field(md_text, "source_page_ranges")
    ranges = parse_ranges(src_ranges_spec or "")

    doc = fitz.open(str(pdf_path))
    npages = doc.page_count
    hit_pages = []
    hit_pages_broad = []
    for i in range(npages):
        page = doc.load_page(i)
        t = page.get_text()
        n = norm(t)
        if ("금리민감도" in n) or ("위험민감도" in n and "6-8" in n) or ("6-8" in n and "위험민감도" in n):
            hit_pages.append(i + 1)
        elif "민감도분석" in n and "금리" in n:
            hit_pages.append(i + 1)
        elif "6-8" in n and "민감도" in n:
            hit_pages_broad.append(i + 1)
    doc.close()

    all_hits = sorted(set(hit_pages) | set(hit_pages_broad))
    in_window = [p for p in all_hits if in_ranges(p, ranges)] if ranges else []
    out_window = [p for p in all_hits if p not in in_window]
    results[code] = {
        "pdf": pdf_path.name,
        "npages": npages,
        "source_page_ranges": src_ranges_spec,
        "hit_pages_narrow": hit_pages,
        "hit_pages_broad_6-8": hit_pages_broad,
        "in_window": in_window,
        "OUT_OF_WINDOW": out_window,
    }
    status = "NO_HIT" if not all_hits else ("IN_WINDOW" if out_window == [] and in_window else "OUT_OF_WINDOW" if out_window else "?")
    print(f"{code:8s} pages={npages:4d} window={src_ranges_spec!s:14s} hits={all_hits}  -> {status}")

out = REPO / "data" / "_derived" / "_probe_ratesens_pdf_locate.json"
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nwrote {out}")
