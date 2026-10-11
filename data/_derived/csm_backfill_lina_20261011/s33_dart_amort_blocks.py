# -*- coding: utf-8 -*-
"""Step 33 (read-only): the candidate CSM-amortisation blocks that the viz extractor sees for the FY2025 consolidated audit
report of Lina (data/dart/extracted/라이나생명보험_20260406004539_csm.json) and which one _pick_amort_block would choose."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

d = json.loads((ROOT / "data/dart/extracted/라이나생명보험_20260406004539_csm.json").read_text(encoding="utf-8"))
blocks = d if isinstance(d, list) else (d.get("blocks") or d.get("candidates") or [])
print("type", type(d).__name__, "blocks:", len(blocks), "| first block keys:", list(blocks[0].keys()) if blocks else None)
import viz_build_ifrs17_panels as V  # noqa: E402

kw = ("상각", "인식", "예상", "기대", "CSM")
elig = []
for i, b in enumerate(blocks):
    cap = str(b.get("caption") or "")
    if any(k in cap for k in kw) and V.header_has_year_buckets(b.get("header") or []):
        elig.append(b)
        rows = b.get("rows") or []
        hdr = V._flatten_header(b.get("header") or [])
        tot = [r for r in rows if r and "합계" in str(r[0])]
        print(f"  block#{i} line_no={b.get('line_no')} score={b.get('score')} rows={len(rows)} cols={V._bucket_columns_count(b)} basis={V._block_basis(b)} caption={cap[:70]!r}")
        print("      header:", hdr[:12])
        print("      합계 row:", (tot[0][:10] if tot else None))
best = V._pick_amort_block(elig)
print("\n_pick_amort_block chooses line_no", best.get("line_no") if best else None)
