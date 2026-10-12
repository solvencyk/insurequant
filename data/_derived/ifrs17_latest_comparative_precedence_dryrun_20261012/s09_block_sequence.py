"""Read-only probe: print the document-order sequence of measurement blocks for one raw dir, with the builder's own
prior/current flags and extracted stage vectors, to design the 'prior-period (comparative) column' reader.

usage: python s09_block_sequence.py <FYyyyy_Qn> <KR code> [--all]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_csm_waterfall_master as B  # noqa: E402

fy, kr = sys.argv[1], sys.argv[2]
show_all = "--all" in sys.argv
rds = sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*"))
print("dirs", [r.name for r in rds])
for rd in rds:
    name = B.META.get(kr, (kr,))[0]
    blocks = B.blocks_for_dir(rd, name)
    print("==", rd.name, "blocks", len(blocks))
    for i, b in enumerate(sorted(blocks, key=lambda x: (x.get("_src", ""), x.get("line_no") or 0))):
        cap = (b.get("caption") or "")
        rows = b.get("rows") or []
        st = None
        try:
            st = B.block_stages(b)
        except Exception as e:
            st = f"ERR {e}"
        st2 = None
        try:
            st2 = B.pattern2_stages(b)
        except Exception:
            st2 = None
        marker = ""
        if len(rows) <= 2 and rows and isinstance(rows[0][0], str):
            marker = "MARK:" + rows[0][0][:20]
        if not show_all and not (st or st2 or marker):
            continue
        print(f"[{i:02d}] {b.get('_src','')[-14:]} L{b.get('line_no')} n={len(rows)} {marker} pc={B._is_prior_caption(cap)} ph={B._is_prior_header(b)} cap={cap[:60]!r}")
        if st:
            print("      block_stages", st)
        if st2:
            print("      pattern2    ", st2)
