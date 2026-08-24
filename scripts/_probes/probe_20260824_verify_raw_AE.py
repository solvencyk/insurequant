# -*- coding: utf-8 -*-
"""Read-only raw verification for inbox/parser/20260824T0400Z item52-54 defects.
Prints full page text + coordinate-clustered rows (label, x0..x1 per value) for the
TFI memo-row table page(s) of each named bucket, so column (pre/post) assignment can
be confirmed independently of the inbox's quoted numbers.

Usage: python scripts/_probes/probe_20260824_verify_raw_AE.py <CODE> <PDFNAME> [page1based ...]
  If no page given, auto-locates via the same "공통적용"+"보완자본"+"한도" match used
  by fix_20260824_tfi_capital_memo_rows.py.
"""
from __future__ import annotations
import sys, os
from pathlib import Path

sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import fitz  # noqa: E402
fitz.TOOLS.mupdf_display_errors(False)
fitz.TOOLS.mupdf_display_warnings(False)


def cluster_rows(words, ytol=3.0):
    seen = set()
    uniq = []
    for w in words:
        if w[4].strip() == "":
            continue
        key = (round(w[0], 1), round(w[1], 1), round(w[2], 1), round(w[3], 1), w[4])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(w)
    ws = sorted(uniq, key=lambda w: (w[1], w[0]))
    rows = []
    cur, cur_y = [], None
    for w in ws:
        x0, y0, x1, txt = w[0], w[1], w[2], w[4]
        if cur_y is None or abs(y0 - cur_y) <= ytol:
            cur.append((x0, x1, txt))
            cur_y = cur_y if cur_y is not None else y0
        else:
            rows.append((cur_y, sorted(cur, key=lambda t: t[0])))
            cur, cur_y = [(x0, x1, txt)], y0
    if cur:
        rows.append((cur_y, sorted(cur, key=lambda t: t[0])))
    return rows


def main():
    args = sys.argv[1:]
    pdf_rel = args[0]
    pages_1based = [int(a) for a in args[1:]] if len(args) > 1 else None
    pdf_path = REPO / pdf_rel
    if not pdf_path.exists():
        print(f"NOT FOUND: {pdf_path}")
        return 1
    doc = fitz.open(pdf_path)
    print(f"opened {pdf_path.name}, {doc.page_count} pages")
    if pages_1based is None:
        texts = [doc[i].get_text() for i in range(doc.page_count)]
        matched = [i for i, t in enumerate(texts) if "공통적용" in t and "보완자본" in t and "한도" in t]
        pages_1based = [i + 1 for i in matched]
        print(f"auto-matched pages (1-based) = {pages_1based}")
    for p1 in pages_1based:
        pi = p1 - 1
        if pi < 0 or pi >= doc.page_count:
            print(f"page {p1} out of range")
            continue
        page = doc[pi]
        print(f"\n========== page {p1} (0idx {pi}) FULL TEXT ==========")
        print(page.get_text())
        print(f"\n---------- page {p1} CLUSTERED ROWS (coord) ----------")
        for y, toks in cluster_rows(page.get_text("words")):
            label = "".join(t for _x0, _x1, t in toks if not t.replace(",", "").replace(".", "").replace("-", "").isdigit())
            rendered = " | ".join(f"x0={x0:.1f},x1={x1:.1f}:'{t}'" for x0, x1, t in toks)
            print(f"y={y:7.1f}  {rendered}")
    doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
