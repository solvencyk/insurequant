#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diff old (backup, pre-rebuild) vs new (just-rebuilt) IFRS17_BS.json -- identify exactly
which (company, item, quarter) cells are new/changed/removed. Read-only comparison."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SCRATCH = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c5d6e48d-e496-45b2-84e0-4e8c8bb5fb23\scratchpad")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

old = json.loads((SCRATCH / "IFRS17_BS.json.before").read_text(encoding="utf-8"))
new = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


old_idx = {key(r): r["값"] for r in old}
new_idx = {key(r): r["값"] for r in new}

print(f"old rows={len(old)} new rows={len(new)}")

added = sorted(set(new_idx) - set(old_idx))
removed = sorted(set(old_idx) - set(new_idx))
changed = sorted(k for k in (set(old_idx) & set(new_idx)) if old_idx[k] != new_idx[k])

print(f"added={len(added)} removed={len(removed)} changed={len(changed)}")
print()
print("=== ADDED ===")
for k in added:
    print(f"  {k}  -> {new_idx[k]}")
print()
print("=== REMOVED ===")
for k in removed:
    print(f"  {k}  (was {old_idx[k]})")
print()
print("=== CHANGED ===")
for k in changed:
    print(f"  {k}  {old_idx[k]} -> {new_idx[k]}")

# item-8-only counts, both files
old8 = sum(1 for r in old if r["항목번호"] == 8)
new8 = sum(1 for r in new if r["항목번호"] == 8)
print()
print(f"item8 count: old={old8} new={new8}")
