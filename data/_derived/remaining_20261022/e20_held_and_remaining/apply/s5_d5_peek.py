#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 5: peek the d5_buckets.json structure (census facts) for the target buckets -> s5_d5_peek.txt (read-only)"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = ROOT / "data/_derived/remaining_20261022/e20_held_and_remaining/apply/s5_d5_peek.txt"
d5 = json.loads((ROOT / "data/_derived/remaining_20261022/d_census/d5_buckets.json").read_text(encoding="utf-8"))
L = [f"type {type(d5).__name__} len {len(d5)}"]
first = d5[0] if isinstance(d5, list) else None
L.append("keys of first: " + json.dumps(list(first.keys()), ensure_ascii=False))
TARGET = [("KR0082", "2023.1Q"), ("KR0082", "2023.2Q"), ("KR0083", "2024.3Q"), ("KR0087", "2024.4Q"), ("KR0087", "2025.1Q"), ("KR0087", "2025.2Q"),
          ("KR0032", "2023.1Q"), ("KR0104", "2024.4Q"), ("KR0104", "2025.1Q"), ("KR0104", "2025.2Q"), ("KR0069", "2025.1Q"), ("KR0069", "2025.2Q"),
          ("KR0094", "2025.2Q"), ("KR0070", "2025.1Q"), ("KR0070", "2025.2Q"), ("KR0072", "2024.4Q"), ("KR0068", "2024.4Q"), ("KR0068", "2025.1Q"),
          ("KR0068", "2025.2Q"), ("KR0071", "2025.1Q"), ("KR0071", "2025.2Q")]
by = {(b["code"], b["q"]): b for b in d5}
for k in TARGET:
    b = by.get(k)
    if b is None:
        L.append(f"{k}: MISSING in d5")
        continue
    L.append(f"===== {k}: keys {list(b.keys())}")
    for kk, vv in b.items():
        if kk in ("its", "cls"):
            continue
        s = json.dumps(vv, ensure_ascii=False)
        L.append(f"   {kk}: {s[:700]}")
    its = b.get("its", {})
    for i in sorted(its, key=int):
        v = its[i]
        L.append(f"   it {i}: " + json.dumps(v, ensure_ascii=False)[:300])
text = "\n".join(L)
OUT.write_text(text + "\n", encoding="utf-8", newline="\n")
print(len(text))
