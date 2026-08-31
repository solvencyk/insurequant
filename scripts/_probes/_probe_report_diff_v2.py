# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_20260831T051505Z.json", "r", encoding="utf-8") as f:
    before = json.load(f)
with open("artifacts/kics_validation/report_20260831T053313Z.json", "r", encoding="utf-8") as f:
    after = json.load(f)

def key(f):
    return (f["원보험사코드"], f["공시분기"], f["rule"])

before_map = {key(f): f["status"] for f in before["findings"]}
after_map = {key(f): f["status"] for f in after["findings"]}

all_keys = set(before_map) | set(after_map)
changed = [(k, before_map.get(k), after_map.get(k)) for k in all_keys if before_map.get(k) != after_map.get(k)]
changed.sort()
print(f"total changed findings: {len(changed)}")
for k, b, a in changed:
    print(f"  {k[0]} {k[1]} [{k[2]}]: {b} -> {a}")

# any finding NOT about KR0049 that changed?
other_co_changes = [c for c in changed if c[0][0] != "KR0049"]
print(f"\nchanges outside KR0049: {len(other_co_changes)}")
for c in other_co_changes:
    print(" ", c)

# top-level counts
print("\nbefore summary:", before["summary"])
print("after summary:", after["summary"])
