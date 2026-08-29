# -*- coding: utf-8 -*-
"""Dump blocks_for_dir() blocks (caption/header/block_stages) for KR0079 across
several quarters, filtered to blocks whose caption OR header mentions a product-line
token (사망/건강/연금/저축/기타) -- to see whether each quarter's per-product breakdown
is a SINGLE WIDE table (product columns) or SEPARATE per-product blocks (product
captions), and whether "기타" is present/handled either way. Read-only.
"""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir, block_stages, _ns

TARGETS = [
    ("data/dart/FY2025_Q1/raw/KR0079_미래에셋생명", "KR0079_미래에셋생명", "2025.1Q"),
    ("data/dart/FY2025_Q2/raw/KR0079_미래에셋생명", "KR0079_미래에셋생명", "2025.2Q"),
    ("data/dart/FY2025_Q3/raw/KR0079_미래에셋생명", "KR0079_미래에셋생명", "2025.3Q"),
    ("data/dart/FY2026_Q1/raw/KR0079_미래에셋생명", "KR0079_미래에셋생명", "2026.1Q"),
    ("data/dart/FY2026_Q2/raw/KR0079_미래에셋생명", "KR0079_미래에셋생명", "2026.2Q"),
]

PROD_TOK = ("사망", "건강", "연금", "저축", "기타")

lines = []
for rel, name, label in TARGETS:
    rd = ROOT / rel
    if not rd.exists():
        lines.append(f"===== {label} ({rel}) MISSING DIR =====\n")
        continue
    blocks = blocks_for_dir(rd, name)
    lines.append(f"===== {label} ({rel}) -- {len(blocks)} blocks total =====")
    for i, b in enumerate(blocks):
        cap = b.get("caption") or ""
        header = b.get("header") or []
        rows = b.get("rows") or []
        hflat = " | ".join(" ".join(str(c) for c in row) for row in header)
        capn = _ns(cap)
        hn = _ns(hflat)
        if not any(t in capn or t in hn for t in PROD_TOK):
            continue
        st = block_stages(b)
        lines.append(f"--- block {i} src={b.get('_src')} basis={b.get('basis')} ---")
        lines.append(f"  caption: {cap!r}")
        lines.append(f"  header : {hflat[:300]}")
        lines.append(f"  #rows  : {len(rows)}")
        lines.append(f"  block_stages(): {st}")
    lines.append("")

out_path = ROOT / "scripts/_probes/_out_20260830_kr0079_multi_quarter_blocks_dump.txt"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out_path} ({len(lines)} lines)")
