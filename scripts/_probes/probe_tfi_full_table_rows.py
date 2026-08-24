# -*- coding: utf-8 -*-
"""iter-10 probe -- dump EVERY line of the [지급여력비율의 경과조치 적용에 관한 사항]
(1) 공통적용 경과조치 관련 table (구분 ~ 지급여력기준금액) for a handful of companies/quarters,
so we can see the full row list and check nothing beyond 47-51 + memo rows is unmapped.

Read-only. Prints to stdout only.

Usage:
  ...python scripts/_probes/probe_tfi_full_table_rows.py KR0010 2024.1Q
  ...python scripts/_probes/probe_tfi_full_table_rows.py KR0010 2024.1Q KR1000 2023.2Q ...
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "scripts"))

import fitz  # noqa: E402
import fix_20260821_tier2_limit_lines as T2  # noqa: E402


def dump(code: str, q: str):
    pdf = T2._pdf(T2.q2p(q), code)
    print(f"\n{'='*70}\n{code} {q}  pdf={pdf}\n{'='*70}")
    if pdf is None:
        print("  raw 없음")
        return
    doc = fitz.open(pdf)
    try:
        page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    finally:
        doc.close()
    matched = [i for i, t in enumerate(page_texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t]
    if not matched:
        total_chars = sum(len(t) for t in page_texts)
        n = len(page_texts)
        print(f"  '공통적용'+'보완자본'+'한도' 동시 페이지 없음 (density={total_chars/n if n else 0:.1f}자/p, {n}p)")
        return
    for pi in matched:
        print(f"  -- page {pi+1} (matched) --")
    include = set(matched)
    for i in matched:
        if i + 1 < len(page_texts):
            include.add(i + 1)
    lines: list[str] = []
    for i in sorted(include):
        lines.extend(x.strip() for x in page_texts[i].splitlines())
    # locate window: from first '구분' after a '공통적용' line, to first '지급여력기준금액' after that
    start = None
    for i, l in enumerate(lines):
        if "공통적용" in l:
            start = i
            break
    if start is None:
        start = 0
    end = None
    for i in range(start, len(lines)):
        if lines[i].replace(" ", "") == "지급여력기준금액":
            end = i
            break
    if end is None:
        end = min(len(lines), start + 60)
    for i in range(start, min(end + 3, len(lines))):
        marker = ""
        s = lines[i].strip()
        print(f"  {i:3d} {marker}{s!r}")


if __name__ == "__main__":
    args = sys.argv[1:]
    pairs = list(zip(args[0::2], args[1::2]))
    for code, q in pairs:
        dump(code, q)
