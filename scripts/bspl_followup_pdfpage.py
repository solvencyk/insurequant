#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helper for the 2026-10-11 BS/PL follow-up (parser/ifrs17): print the text layer of PDF pages and/or render them to PNG.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_pdfpage.py <pdf> <page[,page...]> [--png OUTDIR] [--dpi 110] [--text] [--grep WORD]

Pages are 1-based.  Read-only on the PDF; PNGs go to OUTDIR (default: the session scratchpad passed explicitly).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("pages", help="comma list of 1-based pages, or a-b ranges")
    ap.add_argument("--png", default="")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--text", action="store_true")
    ap.add_argument("--grep", default="")
    a = ap.parse_args()
    pages = []
    for tok in a.pages.split(","):
        if "-" in tok:
            s, e = tok.split("-")
            pages += list(range(int(s), int(e) + 1))
        elif tok:
            pages.append(int(tok))
    doc = fitz.open(a.pdf)
    print(f"{a.pdf}: {doc.page_count} pages")
    for p in pages:
        if p < 1 or p > doc.page_count:
            print(f"page {p}: out of range")
            continue
        pg = doc[p - 1]
        if a.text or a.grep:
            txt = pg.get_text("text")
            if a.grep:
                for i, ln in enumerate(txt.splitlines()):
                    if a.grep in ln:
                        print(f"p{p} L{i}: {ln}")
            else:
                print(f"----- page {p} text ({len(txt)} chars) -----")
                print(txt)
        if a.png:
            out = Path(a.png)
            out.mkdir(parents=True, exist_ok=True)
            pix = pg.get_pixmap(dpi=a.dpi)
            fn = out / f"{Path(a.pdf).stem}_p{p}.png"
            pix.save(str(fn))
            print("saved", fn, pix.width, "x", pix.height)


if __name__ == "__main__":
    main()
