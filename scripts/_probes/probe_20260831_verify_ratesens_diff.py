#!/usr/bin/env python3
"""Verify only the intended 12 rows changed between backup and current kics_rate_sensitivity.json."""
from __future__ import annotations
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
old = json.loads((ROOT / "kics_rate_sensitivity.json.bak_20260831_ratesens_redfix").read_text(encoding="utf-8"))
new = json.loads((ROOT / "kics_rate_sensitivity.json").read_text(encoding="utf-8"))

print(f"old rows={len(old)} new rows={len(new)}")

def key(r):
    return (r["원수사명"], r["공시분기"], r["경과조치여부"], r["measure구분"])

old_by_key = {key(r): r for r in old}
new_by_key = {key(r): r for r in new}

print(f"old keys={len(old_by_key)} new keys={len(new_by_key)} (dup check: {len(old)==len(old_by_key)}, {len(new)==len(new_by_key)})")
assert set(old_by_key) == set(new_by_key), "KEY SET CHANGED -- ABORT CONCERN"

changed = [k for k in old_by_key if old_by_key[k] != new_by_key[k]]
print(f"changed rows: {len(changed)}")
for k in sorted(changed):
    print(f"  {k}")
