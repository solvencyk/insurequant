#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 1: read-only dump of the structure of the round-18 plan_KR*.json files (buckets incl. held ones, cell schema) -> s1_plan_struct.txt"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
E = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
OUT = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/apply/s1_plan_struct.txt")
L = []
for code in ["KR0082", "KR0083", "KR0087", "KR0104", "KR0032", "KR0070", "KR0005"]:
    p = json.loads((E / f"plan_{code}.json").read_text(encoding="utf-8"))
    L.append(f"===== plan_{code}.json top keys: {list(p.keys())}")
    for k, v in p.items():
        if k in ("cells", "seam_cells"):
            continue
        s = json.dumps(v, ensure_ascii=False)
        L.append(f"  [{k}] ({type(v).__name__}, len {len(s)}) {s[:1500]}")
    if p.get("cells"):
        L.append(f"  cells[0] = {json.dumps(p['cells'][0], ensure_ascii=False)[:1500]}")
        L.append(f"  n cells {len(p['cells'])}")
    if p.get("seam_cells"):
        L.append(f"  seam_cells[0] = {json.dumps(p['seam_cells'][0], ensure_ascii=False)[:900]}")
text = "\n".join(L)
OUT.write_text(text + "\n", encoding="utf-8", newline="\n")
print(len(text))
