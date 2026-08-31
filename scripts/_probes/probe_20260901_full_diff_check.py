# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BEFORE = r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kics_disclosure_scratch_round23.json"
AFTER = "kics_disclosure.json"

def load(p):
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    r = d["records"] if isinstance(d, dict) and "records" in d else d
    idx = {}
    for row in r:
        key = (row.get("원보험사코드"), row.get("공시분기"), row.get("항목번호"))
        idx[key] = (row.get("값"), row.get("값_적용후"))
    return idx

before = load(BEFORE)
after = load(AFTER)

before_keys = set(before)
after_keys = set(after)

inserted = after_keys - before_keys
deleted = before_keys - after_keys
common = before_keys & after_keys
changed = [k for k in common if before[k] != after[k]]

companies_touched = sorted({k[0] for k in inserted} | {k[0] for k in changed} | {k[0] for k in deleted})
print("inserted:", len(inserted), " deleted:", len(deleted), " changed(among common):", len(changed))
print("companies touched:", companies_touched)
print()
print("=== deleted (should be EMPTY) ===")
for k in sorted(deleted):
    print(k)
print()
print("=== any company outside my 7 in inserted/changed? ===")
MY7 = {"KR0009","KR0150","KR0087","KR0083","KR1011","KR0051"}
outside = [k for k in (inserted | set(changed)) if k[0] not in MY7]
print(len(outside), "outside-scope touches")
for k in sorted(outside):
    print(k, "before=", before.get(k), "after=", after.get(k))
