# -*- coding: utf-8 -*-
"""Extract canonical 항목명 strings (byte-exact) for target items from KR0032's own existing rows."""
import sys, io, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0032"]

targets = [19, 23, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54]
labels = {}
for item in targets:
    # take label from most recent quarter that has it
    candidates = sorted([r for r in rows if r["항목번호"] == item], key=lambda r: r["공시분기"], reverse=True)
    if candidates:
        labels[item] = candidates[0]["항목명"]
    else:
        labels[item] = None
    print(f"item{item}: {labels[item]!r}")

with open(r"C:\Users\sangwook.cho\Desktop\insurequant\scripts\_probes\_kr0032_labels.json", "w", encoding="utf-8") as f:
    json.dump(labels, f, ensure_ascii=False, indent=2)
print("wrote _kr0032_labels.json")

# also print 티커/생손보여부 fields to replicate in new rows, and verify item19/23 row identity fields
for item in [19, 23]:
    row = next(r for r in rows if r["항목번호"] == item and r["공시분기"] == "2026.2Q")
    print(f"\nexisting 2026.2Q item{item} row: {json.dumps(row, ensure_ascii=False)}")

# print field skeleton from a full row (e.g. item1 2026.2Q) to replicate key order/fields for new rows
skel = next(r for r in rows if r["항목번호"] == 1 and r["공시분기"] == "2026.2Q")
print(f"\nskeleton (item1 2026.2Q): {json.dumps(skel, ensure_ascii=False)}")
