# -*- coding: utf-8 -*-
"""Replicates extract_tier2()'s line-building + scanning, but prints every step near
item48/item49 so we can see exactly where item49 capture goes wrong."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from fix_20260821_tier2_limit_lines import _pdf, q2p, _collect_values, NUMRE, ZERO, DECOR  # noqa: E402
# (import above already rewraps sys.stdout as utf-8 -- don't double-wrap, it closes the buffer)


def norm(s):
    return s.replace(" ", "")


def main():
    code, q = sys.argv[1], sys.argv[2]
    pdf = _pdf(q2p(q), code)
    doc = fitz.open(pdf)
    page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    matched = {i for i, t in enumerate(page_texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t}
    print(f"matched = {sorted(matched)}")
    include = set(matched)
    for i in matched:
        if i + 1 < len(page_texts):
            include.add(i + 1)
    print(f"include = {sorted(include)}")

    lines: list[str] = []
    for i in sorted(include):
        lines.extend(x.strip() for x in page_texts[i].splitlines())

    print(f"total lines = {len(lines)}")
    # find every occurrence of a line that, normalized, starts with 해약환급금부족분상당액중
    head = norm("해약환급금 부족분 상당액 중")
    hits = [idx for idx, l in enumerate(lines) if norm(l).startswith(head)]
    print(f"'해약환급금부족분상당액중' head hits at line idx = {hits}")
    for h in hits:
        print(f"  context lines[{h-2}:{h+8}] = {lines[max(0,h-2):h+8]}")

    idx48 = [idx for idx, l in enumerate(lines) if norm(l) == norm("보완자본 한도")]
    print(f"'보완자본 한도' exact-match hits at line idx = {idx48}")
    for h in idx48:
        print(f"  context lines[{h}:{h+6}] = {lines[h:h+6]}")
        vals, j = _collect_values(lines, h + 1, need=2)
        print(f"  _collect_values from {h+1} -> vals={vals}, next_idx={j}, lines[j]={lines[j] if j < len(lines) else 'EOF'}")


if __name__ == "__main__":
    raise SystemExit(main())
