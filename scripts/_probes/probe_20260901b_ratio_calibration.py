# -*- coding: utf-8 -*-
"""Calibrate a source_page_ranges-coverage-ratio threshold: for each 2026.2Q
company, compute (selected page count / total PDF page count) and print it
next to the MD_FULL/landmine classification from probe_20260901b_market_window_census.
Read-only; no writes to any master file."""
from __future__ import annotations
import glob
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pypdf import PdfReader  # noqa: E402

MD_DIR = REPO / "md_inbox" / "FY2026_Q2"
PDF_DIR = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf"

LANDMINE_CODES = {
    "KR0002", "KR0010", "KR0011", "KR0032", "KR0049", "KR0051", "KR0068",
    "KR0074", "KR0079", "KR0080", "KR0082", "KR0087", "KR0094", "KR0099",
    "KR0100", "KR0104", "KR1000", "KR1098",
}


def read_front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    _, _, rest = text.partition("---\n")
    front, _, _ = rest.partition("\n---\n")
    meta = {}
    for raw in front.splitlines():
        if ":" not in raw:
            continue
        k, _, v = raw.partition(":")
        meta[k.strip()] = v.strip().strip('"')
    return meta


def range_page_count(spr: str) -> int:
    total = 0
    for part in spr.split(";"):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                total += int(b) - int(a) + 1
            except ValueError:
                pass
        else:
            total += 1
    return total


def main():
    rows = []
    for md_path in sorted(MD_DIR.glob("*.md")):
        code = md_path.stem.split("_", 1)[0]
        meta = read_front_matter(md_path.read_text(encoding="utf-8"))
        spr = meta.get("source_page_ranges", "")
        if not spr:
            continue
        pdfs = glob.glob(str(PDF_DIR / f"{code}_*.pdf"))
        if not pdfs:
            continue
        try:
            total_pages = len(PdfReader(pdfs[0]).pages)
        except Exception as e:
            print(f"{code}: pdf read error {e}")
            continue
        selected = range_page_count(spr)
        ratio = selected / total_pages if total_pages else 0
        tag = "LANDMINE" if code in LANDMINE_CODES else "ok"
        rows.append((ratio, code, selected, total_pages, tag, meta.get("quarter", "")))

    rows.sort()
    print(f"{'ratio':>6} {'code':8} {'sel':>4}/{'tot':<4} {'tag':10} quarter")
    for ratio, code, selected, total_pages, tag, q in rows:
        print(f"{ratio:6.2%} {code:8} {selected:4}/{total_pages:<4} {tag:10} {q}")

    ok_ratios = [r for r, c, s, t, tag, q in rows if tag == "ok"]
    lm_ratios = [r for r, c, s, t, tag, q in rows if tag == "LANDMINE"]
    if ok_ratios:
        print(f"\nok:       n={len(ok_ratios)} min={min(ok_ratios):.2%} median={sorted(ok_ratios)[len(ok_ratios)//2]:.2%} max={max(ok_ratios):.2%}")
    if lm_ratios:
        print(f"landmine: n={len(lm_ratios)} min={min(lm_ratios):.2%} median={sorted(lm_ratios)[len(lm_ratios)//2]:.2%} max={max(lm_ratios):.2%}")


if __name__ == "__main__":
    main()
