#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B5): contact sheet of PDF pages to locate a statement page in an image-only PDF (read-only).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_montage.py <FYxxxx_Qn> <KR####> <first>-<last> [--cols 4] [--dpi 55] [--pick substring] [--out file.png]
The PDF is found by globbing data/disclosure/<FY>/raw/<KR####>_*.pdf (+ attachments/ with --att); --pick selects among several by file-name substring.
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
SCR = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/e15a5832-0270-4430-8e3e-4cba8a1f182c/scratchpad/img")


def main():
    a = sys.argv[1:]
    fy, code, rng = a[0], a[1], a[2]
    cols = int(a[a.index("--cols") + 1]) if "--cols" in a else 4
    dpi = int(a[a.index("--dpi") + 1]) if "--dpi" in a else 55
    pick = a[a.index("--pick") + 1] if "--pick" in a else None
    sub = "attachments" if "--att" in a else "raw"
    files = sorted((ROOT / "data" / "disclosure" / fy / sub).glob(f"{code}_*.pdf"))
    if pick:
        files = [f for f in files if pick in f.name]
    if not files:
        raise SystemExit("no pdf")
    pdf = files[0]
    p0, p1 = [int(x) for x in rng.split("-")]
    doc = fitz.open(str(pdf))
    ims = []
    for p in range(p0, p1 + 1):
        pix = doc[p - 1].get_pixmap(dpi=dpi)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 60, 22], fill=(255, 255, 0))
        d.text((4, 4), f"p{p}", fill=(0, 0, 0))
        ims.append(im)
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), (255, 255, 255))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    out = Path(a[a.index("--out") + 1]) if "--out" in a else SCR / f"montage_{code}_{fy}_{p0}-{p1}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(str(out))
    print(pdf.name, "pages", len(doc), "->", out, sheet.size)


if __name__ == "__main__":
    main()
