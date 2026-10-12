"""Read-only: print row labels (first 2 cells) + first numeric cell of the blocks of one filing that are labelled prior/current.
usage: python s24_dump_block_rows.py <KR> <later_q> [prior|current] [--idx N]
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import prior_csm as P  # noqa: E402

B = P.B
kr, lq = sys.argv[1], sys.argv[2]
which = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] in ("prior", "current") else None
idx = int(sys.argv[sys.argv.index("--idx") + 1]) if "--idx" in sys.argv else None
fy = f"FY{lq[:4]}_Q{lq[5]}"
name = B.META.get(kr, (kr,))[0]
for rd in sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*")):
    blocks = B.blocks_for_dir(rd, name)
    lab = P.label_blocks(blocks)
    k = 0
    for b, l in lab:
        if l == "marker":
            continue
        if which and l != which:
            continue
        if idx is not None and k != idx:
            k += 1
            continue
        k += 1
        print(f"--- [{l}] L{b.get('line_no')} cap={(b.get('caption') or '')[:90]!r}")
        for h in (b.get("header") or [])[:3]:
            print("   H", h)
        for r in (b.get("rows") or [])[:40]:
            print("   R", [str(c)[:22] for c in r[:5]])
