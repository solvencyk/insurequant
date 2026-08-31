# -*- coding: utf-8 -*-
"""Probe: 2026.2Q item47-54 census per company, incl. item48==item3 contamination check."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "kics_disclosure.json", encoding="utf-8") as f:
    rows = json.load(f)

Q = "2026.2Q"
by_bucket = {}
for r in rows:
    if r.get("공시분기") != Q:
        continue
    key = (r["원보험사코드"], r["원수사명"])
    by_bucket.setdefault(key, {})[r["항목번호"]] = r

print(f"=== {Q} buckets: {len(by_bucket)} ===")
print()
TFI = [47, 48, 49, 50, 51, 52, 53, 54]
missing_summary = {}
contaminated = []
for (code, name), items in sorted(by_bucket.items()):
    present = [i for i in TFI if i in items]
    missing = [i for i in TFI if i not in items]
    i3 = items.get(3, {}).get("값")
    i48 = items.get(48, {}).get("값")
    flag = ""
    if i48 is not None and i3 is not None and i48 == i3:
        flag = " <<< item48==item3 (CONTAMINATED SUSPECT)"
        contaminated.append((code, name))
    print(f"{code} {name:14s} present={present} missing={missing}{flag}")
    missing_summary[(code, name)] = missing

print()
n_full = sum(1 for m in missing_summary.values() if not m)
n_none = sum(1 for m in missing_summary.values() if len(m) == len(TFI))
n_partial = len(missing_summary) - n_full - n_none
print(f"full={n_full} none={n_none} partial={n_partial}")
print()
print("item48==item3 suspects:", contaminated)
