# -*- coding: utf-8 -*-
"""Dump ALL blocks_for_dir() blocks for KR0079 2025.4Q (annual) -- caption, header,
and block_stages() result -- to see whether the per-product breakdown is 5 SEPARATE
blocks or ONE WIDE table, and which blocks survive/fail block_stages(). Read-only:
only imports blocks_for_dir/block_stages, no main()/build_csm_waterfall_master.py run.
"""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir, block_stages, _ns

rd = ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664"
name = "KR0079_미래에셋생명"
blocks = blocks_for_dir(rd, name)
lines = [f"{len(blocks)} blocks total\n"]
for i, b in enumerate(blocks):
    cap = b.get("caption") or ""
    header = b.get("header") or []
    rows = b.get("rows") or []
    hflat = " | ".join(" ".join(str(c) for c in row) for row in header)
    st = block_stages(b)
    lines.append(f"--- block {i} src={b.get('_src')} basis={b.get('basis')} ---")
    lines.append(f"  caption: {cap!r}")
    lines.append(f"  header : {hflat[:300]}")
    lines.append(f"  #rows  : {len(rows)}")
    if rows:
        lines.append(f"  row0   : {rows[0]}")
    lines.append(f"  block_stages(): {st}")
    lines.append("")

out_path = ROOT / "scripts/_probes/_out_20260830_kr0079_2025q4_blocks_dump.txt"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out_path} ({len(lines)} lines)")
