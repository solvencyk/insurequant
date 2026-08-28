"""Full census diff of root PL_breakdown.json before vs after running build_pl() to
propagate the KR0079 2026.2Q item6/item7 patch -- confirms the ONLY changed keys are the
ones this ticket intends to touch (item6/item7/값_당분기 for KR0079 2026.2Q, plus whatever
그 quarter's downstream 당분기 dependents), with zero unrelated drift.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
SCRATCH = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c5d6e48d-e496-45b2-84e0-4e8c8bb5fb23\scratchpad")

before = json.loads((SCRATCH / "PL_breakdown_before.json").read_text(encoding="utf-8"))
after = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))

print(f"before rows: {len(before)}  after rows: {len(after)}")

def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])

b = {key(r): r for r in before}
a = {key(r): r for r in after}

only_before = set(b) - set(a)
only_after = set(a) - set(b)
print(f"rows only in before (dropped): {len(only_before)}")
print(f"rows only in after (added): {len(only_after)}")
if only_before:
    print("  sample dropped:", list(only_before)[:10])
if only_after:
    print("  sample added:", list(only_after)[:10])

changed = []
for k in set(b) & set(a):
    rb, ra = b[k], a[k]
    if rb.get("값") != ra.get("값") or rb.get("값_당분기") != ra.get("값_당분기"):
        changed.append((k, rb.get("값"), ra.get("값"), rb.get("값_당분기"), ra.get("값_당분기")))

print(f"\ntotal changed cells (값 or 값_당분기 differs): {len(changed)}")
by_company = {}
for k, *_ in changed:
    by_company.setdefault(k[0], 0)
    by_company[k[0]] += 1
print("changed cells by company code:", by_company)

print("\n--- KR0079 changed rows in detail ---")
for k, ov, nv, od, nd in changed:
    if k[0] == "KR0079":
        print(f"  item{k[1]} {k[2]}: 값 {ov} -> {nv}   값_당분기 {od} -> {nd}")

non_kr0079 = [c for c in changed if c[0][0] != "KR0079"]
print(f"\nnon-KR0079 changed cells: {len(non_kr0079)}")
if non_kr0079:
    print("  SAMPLE (first 20):", non_kr0079[:20])
