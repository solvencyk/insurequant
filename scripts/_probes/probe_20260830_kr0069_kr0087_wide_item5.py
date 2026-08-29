# -*- coding: utf-8 -*-
"""Check KR0069 (삼성생명) 2025.2Q and KR0087 (동양생명) 2025.2Q WIDE product-segmented
blocks for the item5 (CSM amortization) row: does block_stages() get None, and what is
the actual raw row label text? Read-only.
"""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir, block_stages, META
from viz_build_csm_waterfall import find_product_segmented_csm_cols, filter_current_period_rows, row_value_start, rollforward_row_stub

TARGETS = [
    ("KR0069", "data/dart/FY2025_Q2/raw"),
    ("KR0087", "data/dart/FY2025_Q2/raw"),
]

lines = []
for kr, rel in TARGETS:
    name = META.get(kr, (kr, None, None))[0]
    cands = list((ROOT / rel).glob(f"{kr}_*"))
    if not cands:
        lines.append(f"{kr}: no raw dir under {rel}")
        continue
    rd = cands[0]
    blocks = blocks_for_dir(rd, name)
    lines.append(f"===== {kr} {name} ({rd.name}) -- {len(blocks)} blocks =====")
    for i, b in enumerate(blocks):
        hdr = b.get("header") or []
        rows = b.get("rows") or []
        cols = find_product_segmented_csm_cols(hdr, rows)
        if not cols:
            continue
        st = block_stages(b)
        lines.append(f"--- block {i} src={b.get('_src')} cols={cols} ---")
        lines.append(f"  caption: {(b.get('caption') or '')!r}")
        lines.append(f"  block_stages(): {st}")
        # print all row stubs (labels) to find the amortization-looking row
        cur_rows = filter_current_period_rows(rows)
        for r in cur_rows:
            if not r or not isinstance(r[0], str):
                continue
            stub = rollforward_row_stub(r)
            if "보험계약마진" in stub or "당기손익" in stub:
                lines.append(f"    row label: {stub!r}")
    lines.append("")

out_path = ROOT / "scripts/_probes/_out_20260830_kr0069_kr0087_wide_item5.txt"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out_path}")
