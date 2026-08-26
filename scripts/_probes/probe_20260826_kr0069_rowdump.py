#!/usr/bin/env python3
"""KR0069 picked-block row dump (labels + numeric cells) — item3 검산."""
import sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_csm_waterfall_master as B
from viz_build_csm_waterfall import row_value_start, parse_num

q, want = sys.argv[1], [int(x) for x in sys.argv[2].split(",")]
rd = sorted((ROOT / "data" / "dart" / q / "raw").glob("KR0069_*"))[0]
blocks = B.blocks_for_dir(rd, "삼성생명")
for i in want:
    b = blocks[i]
    print("=" * 90)
    print(f"block[{i}] cap={(b.get('caption') or '')[:80]!r}")
    for hr in (b.get("header") or []):
        print("  HDR:", [str(c)[:24] for c in hr])
    for r in (b.get("rows") or []):
        vs = row_value_start(r)
        lab = " | ".join(str(c) for c in r[:vs] if isinstance(c, str) and str(c).strip())
        nums = [parse_num(x) for x in r[vs:]]
        print(f"  {lab[:46]:46s} {nums}")
