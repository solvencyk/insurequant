# -*- coding: utf-8 -*-
"""RED-63 investigation: does the '1) 공통적용 경과조치' table really print 0/0 for
tier2-limit rows at companies whose item3(보완자본) is large (메트라이프/카카오페이/신한이지)?
Prints the raw matched-page text verbatim so we can see exactly what's on the page,
and optionally renders the page(s) to PNG for visual (vision) confirmation.

Usage:
  ...python scripts/_probes/probe_20260821b_tier2_zero_check.py KR0095 2023.1Q
  ...python scripts/_probes/probe_20260821b_tier2_zero_check.py KR0095 2023.1Q --render
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DISCLOSURE = REPO / "data" / "disclosure"


def q2p(q):
    y, qq = q.split(".")
    return f"FY{y}_Q{qq[0]}"


def find_pdf(period: str, code: str):
    raw = DISCLOSURE / period / "raw"
    pdfs = sorted(raw.glob(f"{code}_*.pdf"))
    if not pdfs:
        return None
    am = [p for p in pdfs if "_amended" in p.name]
    return max(am or pdfs, key=lambda p: p.stat().st_size)


def main():
    code = sys.argv[1]
    q = sys.argv[2]
    render = "--render" in sys.argv
    pdf = find_pdf(q2p(q), code)
    if pdf is None:
        print(f"NO PDF for {code} {q}")
        return 1
    print(f"PDF = {pdf}")
    doc = fitz.open(pdf)
    page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    matched = [i for i, t in enumerate(page_texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t]
    print(f"matched pages (0-indexed) = {matched}")
    for i in matched:
        print(f"\n===== PAGE {i} (printed page ~{i+1}) =====")
        print(page_texts[i])
        if i + 1 < len(page_texts):
            print(f"\n----- PAGE {i+1} (next page, also scanned) -----")
            print(page_texts[i + 1])
        if render:
            for pi in (i, i + 1):
                if pi >= len(doc):
                    continue
                pix = doc[pi].get_pixmap(dpi=240)
                out = REPO / "data" / "_derived" / f"_render_{code}_{q}_p{pi}.png"
                out.parent.mkdir(parents=True, exist_ok=True)
                pix.save(str(out))
                print(f"rendered -> {out}")
    doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
