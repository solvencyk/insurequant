"""Read-only: try the prior-column reader on one filing with several anchor choices and print every candidate block.
usage: python s23_try_prior.py <KR> <later_q> [anchor ...]   (anchor in 억; 'none' for None)
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
anchors = [None if a == "none" else float(a) for a in sys.argv[3:]] or [None]
fy = f"FY{lq[:4]}_Q{lq[5]}"
name = B.META.get(kr, (kr,))[0]
for rd in sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*")):
    pri, cur, blocks, lab = P.prior_blocks(rd, name)
    print("==", rd.name, "blocks", len(blocks), "prior", len(pri), "cur", len(cur))
    for b, l in lab:
        if l == "marker":
            continue
        try:
            st = B.block_stages(b)
        except Exception:
            st = None
        try:
            st2 = B.pattern2_stages(b)
        except Exception:
            st2 = None
        print(f"  [{l:8s}] L{b.get('line_no')} cap={(b.get('caption') or '')[:70]!r} stages={st} p2={st2}")
    for a in anchors:
        wf, src = B.waterfall(pri, a, kr)
        print("  anchor", a, "->", src, wf)
        if wf:
            v, tag = P.stages_to_eok(wf, rd)
            print("      eok", v, tag)
