#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17): print / render pages of the disclosure PDF that Stage A used for (company, quarter).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_stagea_page.py KR0050 2024.1Q 11[,12] [--png OUTDIR] [--dpi 100] [--max 1500]

Read-only.  Text is printed compactly (newlines -> ' | ').  PNG paths are printed so that they can be opened with an image viewer.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)


def main():
    code, q, pages = sys.argv[1], sys.argv[2], sys.argv[3]
    png = sys.argv[sys.argv.index("--png") + 1] if "--png" in sys.argv else ""
    dpi = int(sys.argv[sys.argv.index("--dpi") + 1]) if "--dpi" in sys.argv else 100
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 1500
    d = json.loads((ROOT / "data/_derived/bspl_granularity_20261011/tables" / f"{code}_{q}.json").read_text(encoding="utf-8"))
    pdf = ROOT / d["pdf"]
    doc = fitz.open(pdf)
    print("PDF:", d["pdf"], "pages", doc.page_count)
    for tok in pages.split(","):
        p = int(tok)
        pg = doc[p - 1]
        txt = " | ".join(x.strip() for x in pg.get_text().splitlines() if x.strip())
        print(f"--- p{p} ({len(txt)} chars): {txt[:mx]}")
        if png:
            out = Path(png)
            out.mkdir(parents=True, exist_ok=True)
            fn = out / f"{code}_{q}_p{p}.png"
            pg.get_pixmap(dpi=dpi).save(str(fn))
            print("PNG:", fn)


if __name__ == "__main__":
    main()
