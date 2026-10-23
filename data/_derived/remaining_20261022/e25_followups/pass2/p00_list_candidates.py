# -*- coding: utf-8 -*-
"""pass2 step 0 (read-only): print the sweep candidates for the companies named in ticket 20261024T0300Z, compactly.
Inputs: sweep_neighbors/mismatches.csv (round 1) and sweep_neighbors2/mismatches_part2.csv (round 2)."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
EV = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups")
CODES = {"KR0070", "KR0009", "KR0087", "KR0068", "KR0079", "KR0005", "KR0032", "KR0082", "KR0099"}

print("=== round 1 (mismatches.csv) ===")
with open(EV / "sweep_neighbors" / "mismatches.csv", encoding="utf-8-sig", newline="") as f:
    rows1 = list(csv.DictReader(f))
print("rows", len(rows1))
for r in sorted(rows1, key=lambda r: (r["company"], r["quarter"], r["sheet"], str(r["item"]))):
    if r["company"] not in CODES:
        continue
    print(f"{r['company']} {r['quarter']} {r['sheet']:3s} item {r['item']:>5s} master {r['master']:>12s} latest {r['latest_comparative']:>12s} diff {r['diff_mn']:>10s} {r['cls']:22s} {r['confidence']:6s} moved={r['moved_in_bucket']} | {r['filing'][-45:]} | {r['xml_line']}")

print()
print("=== round 2 (mismatches_part2.csv) ===")
with open(EV / "sweep_neighbors2" / "mismatches_part2.csv", encoding="utf-8-sig", newline="") as f:
    rows2 = list(csv.DictReader(f))
print("rows", len(rows2))
for r in sorted(rows2, key=lambda r: (r["company"], r["quarter"], str(r["item"]))):
    if r["company"] not in CODES:
        continue
    print(f"{r['company']} {r['quarter']} item {r['item']:>5s} master {r['master']:>12s} latest {r['latest']:>12s} diff {r['diff_mn']:>10s} {r['cls'][:34]:34s} {r['confidence']:6s} | {r['filing'][-50:]} | {r['line']} | {r['source']}")
