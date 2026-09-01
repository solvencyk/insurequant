"""Check that export_to_markdown(page_no=N) reassembly loses nothing.

Converts one range, then compares:
  plain        = document.export_to_markdown()
  reassembled  = "\n\n".join(export_to_markdown(page_no=p) for p in pages)
Reports lengths and whether every 4+ digit grouped number in `plain` survives.

Usage: probe_20260901_pagewise_export_check.py KR0051 5 35
"""

from __future__ import annotations

import io
import logging
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
logging.basicConfig(level=logging.ERROR)

PDF_DIR = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf"
NUM_RE = re.compile(r"\d{1,3}(?:,\d{3})+")


def main() -> int:
    code = sys.argv[1]
    lo, hi = int(sys.argv[2]), int(sys.argv[3])
    pdf = sorted(PDF_DIR.glob(f"{code}_*.pdf"))[0]
    from solvency.parser.docling_parser import _get_docling_converter

    conv = _get_docling_converter()
    res = conv.convert(str(pdf), page_range=(lo, hi))
    doc = res.document
    plain = doc.export_to_markdown()
    pages = sorted(getattr(doc, "pages", {}) or {})
    segs = []
    for p in pages:
        try:
            s = doc.export_to_markdown(page_no=p)
        except Exception as exc:  # noqa: BLE001
            print(f"  p{p} export failed: {exc}")
            s = ""
        segs.append((p, s))
    reassembled = "\n\n".join(s for _, s in segs if s.strip())
    print(f"status={res.status}")
    print(f"plain len       = {len(plain):,}")
    print(f"reassembled len = {len(reassembled):,}")
    pn = set(NUM_RE.findall(plain))
    rn = set(NUM_RE.findall(reassembled))
    print(f"numbers plain={len(pn)} reassembled={len(rn)} lost={len(pn - rn)}")
    if pn - rn:
        print("  lost sample:", sorted(pn - rn)[:15])
    print("\nper page md len:")
    for p, s in segs:
        print(f"  p{p:<4} {len(s)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
