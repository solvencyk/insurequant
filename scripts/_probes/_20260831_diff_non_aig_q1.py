# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
before = json.loads((ROOT / "kics_disclosure.json.bak_20260831_aig_backfill").read_text(encoding="utf-8"))
after = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

def key(r):
    return (r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호"))

before_keys = {key(r) for r in before}
after_keys = {key(r) for r in after}

added = after_keys - before_keys
removed = before_keys - after_keys
print(f"ADDED cells: {len(added)}")
for k in sorted(added):
    print(" ADD", k)
print(f"REMOVED cells: {len(removed)}")
for k in sorted(removed):
    print(" REM", k)

# check value changes for cells present in both
before_map = {key(r): r for r in before}
after_map = {key(r): r for r in after}
changed = []
for k in (before_keys & after_keys):
    b, a = before_map[k], after_map[k]
    if b.get("값") != a.get("값") or b.get("값_적용후") != a.get("값_적용후"):
        changed.append((k, b.get("값"), a.get("값"), b.get("값_적용후"), a.get("값_적용후")))
print(f"CHANGED existing cells: {len(changed)}")
for c in changed:
    print(" CHG", c)
