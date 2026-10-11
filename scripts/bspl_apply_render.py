#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B3/B5): render pages of a management-disclosure PDF (or attachment) to PNG for visual reading (read-only on the PDF).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_render.py KR0075 2023.1Q 23,24 [--dpi 170] [--out DIR] [--pdf PATH]
         [--crop x0,y0,x1,y1]       fractions of the page (0..1), e.g. 0,0.08,1,0.55 = the upper half below the header
         [--split N]                cut the (cropped) page into N horizontal bands, written as _b1.._bN (overlap 3%)
Resolves data/disclosure/FY<Y>_Q<n>/raw/KR####_*.pdf (the plain file, not _v... editions) unless --pdf is given.  Prints the PNG paths.
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

from _disclosure_pdf_paths import disclosure_pdfs

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
SCR = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/e15a5832-0270-4430-8e3e-4cba8a1f182c/scratchpad/img")


def resolve(code: str, quarter: str) -> Path:
    y, n = quarter.split(".")
    allp = disclosure_pdfs(f"FY{y}_Q{n[0]}", code)
    cands = [p for p in allp if "_v20" not in p.name and "_amended" not in p.name and "_old" not in p.name]
    if not cands:
        cands = allp
    if not cands:
        raise SystemExit(f"no raw pdf for {code} {quarter}")
    return cands[0]


def pages_arg(s: str):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main():
    a = sys.argv[1:]
    code, quarter, pages = a[0], a[1], pages_arg(a[2])
    dpi = int(a[a.index("--dpi") + 1]) if "--dpi" in a else 170
    out = Path(a[a.index("--out") + 1]) if "--out" in a else SCR
    pdf = Path(a[a.index("--pdf") + 1]) if "--pdf" in a else resolve(code, quarter)
    crop = [float(x) for x in a[a.index("--crop") + 1].split(",")] if "--crop" in a else [0.0, 0.0, 1.0, 1.0]
    split = int(a[a.index("--split") + 1]) if "--split" in a else 1
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf))
    print("pdf:", pdf.name, "pages", len(doc))
    for p in pages:
        page = doc[p - 1]
        r = page.rect
        x0, y0, x1, y1 = r.x0 + crop[0] * r.width, r.y0 + crop[1] * r.height, r.x0 + crop[2] * r.width, r.y0 + crop[3] * r.height
        h = (y1 - y0) / split
        for i in range(split):
            ya = y0 + i * h - (0.03 * h if i else 0.0)
            yb = y0 + (i + 1) * h + (0.03 * h if i < split - 1 else 0.0)
            clip = fitz.Rect(x0, ya, x1, yb)
            pix = page.get_pixmap(dpi=dpi, clip=clip)
            name = f"{code}_{quarter.replace('.', '')}_p{p}" + (f"_b{i + 1}" if split > 1 else "") + ".png"
            pix.save(str(out / name))
            print(f"  {out / name}  {pix.width}x{pix.height}")


if __name__ == "__main__":
    main()
