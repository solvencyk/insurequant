# -*- coding: utf-8 -*-
"""Diagnostic: dump CSM-rollforward candidate blocks for 한화생명/삼성생명 2024.4Q
so we can see what distinguishes 별도 vs 연결 (한화) and per-segment tables (삼성)."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from build_csm_waterfall_master import (blocks_for_dir, block_stages, pattern2_stages,
    _reins_header, _ns, _EXCLUDE_KW)

CASES = {
    "한화생명": ("KR0068", ROOT / "data/dart/FY2024_Q4/raw/KR0068_한화생명_20250312000939"),
    "삼성생명": ("KR0069", ROOT / "data/dart/FY2024_Q4/raw/KR0069_삼성생명_20250312001063"),
}

for name, (kr, rd) in CASES.items():
    print(f"\n{'='*90}\n{name} 2024.4Q  ({rd.name})\n{'='*90}")
    blocks = blocks_for_dir(rd, name)
    print(f"total blocks: {len(blocks)}")
    for i, b in enumerate(blocks):
        cap = (b.get("caption") or "").strip()
        src = b.get("_src", "")
        st = block_stages(b)
        p2 = pattern2_stages(b)
        reins = _reins_header(b)
        ctxn = _ns(cap) + _ns(" ".join(" ".join(str(c) for c in row) for row in (b.get("header") or [])))
        excl = [k for k in _EXCLUDE_KW if k in ctxn]
        # only show blocks that look like CSM rollforwards (have stages or p2)
        if not st and not p2:
            continue
        op = (st or {}).get(1)
        cl = (st or {}).get(6)
        print(f"\n[{i}] src={src} reins={reins} excl={excl}")
        print(f"    caption: {cap[:80]}")
        # header text (first 2 rows)
        hdr = b.get("header") or []
        for hr in hdr[:2]:
            print(f"    hdr: {' | '.join(str(c)[:24] for c in hr)[:120]}")
        if st:
            print(f"    block_stages: open={op} close={cl} nb={st.get(2)} int={st.get(3)} amort={st.get(5)}")
        if p2:
            print(f"    pattern2: open={p2.get(1)} close={p2.get(6)} nb={p2.get(2)} int={p2.get(3)} amort={p2.get(5)}")
