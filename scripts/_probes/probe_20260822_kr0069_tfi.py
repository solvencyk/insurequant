# -*- coding: utf-8 -*-
"""Read-only investigation probe: KR0069 (삼성생명) FY2025_Q4 TFI (공통적용경과조치) table.

Step 1: locate the page(s) where '공통적용'+'보완자본'+'한도' co-occur, mirroring
extract_tfi_full's page-matching logic (fix_20260822_tfi_tier_full_scan.py), but
standalone so we don't import that module (avoids the stdout-rewrap collision noted
in the task instructions) and so we can inspect intermediate state freely.

Usage:
  .../python.exe scripts/_probes/probe_20260822_kr0069_tfi.py step1
  .../python.exe scripts/_probes/probe_20260822_kr0069_tfi.py step2
  .../python.exe scripts/_probes/probe_20260822_kr0069_tfi.py step3
  .../python.exe scripts/_probes/probe_20260822_kr0069_tfi.py step3b
  .../python.exe scripts/_probes/probe_20260822_kr0069_tfi.py step4
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # noqa: E402

PDF = REPO / "data" / "disclosure" / "FY2025_Q4" / "raw" / "KR0069_삼성생명.pdf"


def step1():
    doc = fitz.open(PDF)
    try:
        page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    finally:
        doc.close()

    print(f"total pages = {len(page_texts)}")
    matched = [i for i, t in enumerate(page_texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t]
    print(f"matched pages (0-indexed) = {matched}")
    print(f"matched pages (1-indexed, human) = {[i+1 for i in matched]}")
    for i in matched:
        t = page_texts[i]
        print(f"--- page idx {i} (human p.{i+1}) len={len(t)} chars ---")
        print(f"   '공통적용' count={t.count('공통적용')}  '보완자본' count={t.count('보완자본')}  "
              f"'한도' count={t.count('한도')}  '기본자본' count={t.count('기본자본')}  "
              f"'지급여력기준금액' count={t.count('지급여력기준금액')}")


def step2():
    """Dump raw get_text() for page idx 56 and 57 (matched + matched+1), line by line
    with index numbers, to see the actual print order (label-before-value vs value-before-label)."""
    doc = fitz.open(PDF)
    try:
        for i in (56, 57):
            t = doc[i].get_text()
            print(f"===== PAGE idx {i} (human p.{i+1}) RAW get_text() =====")
            lines = t.splitlines()
            for n, l in enumerate(lines):
                print(f"[{n:3d}] {l!r}")
            print(f"===== end page idx {i}, {len(lines)} lines =====\n")
    finally:
        doc.close()


def step3():
    """Coordinate-based reconstruction of page idx 56 (human p.57): group words by
    (block_no, line_no) as fitz computes them, print each line's words sorted by x0
    with full coordinates, so we can see the physical row/column layout independent
    of get_text() stream order."""
    doc = fitz.open(PDF)
    try:
        page = doc[56]
        words = page.get_text("words")  # (x0,y0,x1,y1,text,block_no,line_no,word_no)
        print(f"page idx 56 (human p.57): {len(words)} words")
        from collections import defaultdict
        groups = defaultdict(list)
        for w in words:
            x0, y0, x1, y1, text, block_no, line_no, word_no = w
            groups[(block_no, line_no)].append((x0, y0, x1, y1, text, word_no))
        for key in sorted(groups.keys()):
            items = sorted(groups[key], key=lambda t: t[0])
            avg_y = sum(t[1] for t in items) / len(items)
            joined = " | ".join(f"{t[4]!r}@x{t[0]:.1f}" for t in items)
            print(f"block{key[0]:3d} line{key[1]:2d} y~{avg_y:6.1f}: {joined}")
    finally:
        doc.close()


def step3b():
    """Pure y-coordinate clustering (ignore fitz block/line grouping entirely) to
    double-check row structure independent of fitz's own line segmentation. Rounds
    y0 to nearest integer and groups words whose rounded y0 matches, then sorts by x0."""
    doc = fitz.open(PDF)
    try:
        page = doc[56]
        words = page.get_text("words")
        from collections import defaultdict
        rows = defaultdict(list)
        for w in words:
            x0, y0, x1, y1, text, block_no, line_no, word_no = w
            key = round(y0)
            rows[key].append((x0, y1, text))
        print(f"page idx 56: {len(rows)} distinct rounded-y0 rows, {len(words)} words total")
        for y in sorted(rows.keys()):
            items = sorted(rows[y], key=lambda t: t[0])
            joined = " | ".join(f"{t[2]!r}@x{t[0]:.1f}" for t in items)
            print(f"y={y:4d}: {joined}")
    finally:
        doc.close()


def step4():
    """Self-check arithmetic using the coordinate-confirmed (value,value,label) row
    reading, printed cleanly for the report."""
    rows = [
        ("지급여력비율(%)", 198.0, 198.0),
        ("지급여력금액", 65_740_178, 65_740_178),
        ("기본자본 [item50]", 51_774_332, 51_774_332),
        ("보완자본 [item51]", 13_965_846, 13_965_846),
        ("보완자본한도적용전 [item47]", 6_628_879, 6_628_879),
        ("보완자본한도 [item48]", 16_603_763, 16_603_763),
        ("해약환급금부족분상당액중초과분 [item49]", 7_336_968, 7_336_968),
        ("(기발행신종자본증권, info)", 0, 0),
        ("(기발행후순위채무, info)", 0, 0),
        ("지급여력기준금액 [anchor~item14]", 33_207_526, 33_207_526),
    ]
    for label, post, pre in rows:
        print(f"{label:42s}  전={pre:>14,.1f}  후={post:>14,.1f}")

    item1_master_eok = 657_402
    item14_master_eok = 332_075
    scr_thispage = 33_207_526
    item50, item51 = 51_774_332, 13_965_846
    item47, item48, item49 = 6_628_879, 16_603_763, 7_336_968

    print("\n--- self-check ---")
    print(f"item50+item51 = {item50+item51:,.1f}  vs  page's own 지급여력금액 = 65,740,178.0"
          f"  diff={item50+item51-65_740_178:,.1f}")
    print(f"page 지급여력금액 / 100 = {65_740_178/100:,.2f} (억원)  vs master item1 = {item1_master_eok:,} (억원)"
          f"  diff={65_740_178/100 - item1_master_eok:,.2f}")
    print(f"item48 = {item48:,.1f}  vs  SCR(thispage)*0.5 = {scr_thispage*0.5:,.1f}"
          f"  diff={item48 - scr_thispage*0.5:,.1f}")
    print(f"page 지급여력기준금액 / 100 = {scr_thispage/100:,.2f} (억원)  vs master item14 = {item14_master_eok:,} (억원)"
          f"  diff={scr_thispage/100 - item14_master_eok:,.2f}")


def render():
    doc = fitz.open(PDF)
    try:
        page = doc[56]
        pix = page.get_pixmap(dpi=250)
        out = REPO / "scripts" / "_probes" / "kr0069_2025q4_p57_tfi.png"
        pix.save(str(out))
        print(f"saved {out} ({pix.width}x{pix.height})")
    finally:
        doc.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "step1"
    fn = {"step1": step1, "step2": step2, "step3": step3, "step3b": step3b,
          "step4": step4, "render": render}.get(cmd)
    if fn is None:
        print(f"unknown cmd {cmd}")
    else:
        fn()
