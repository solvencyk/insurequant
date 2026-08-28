"""Full closing audit for inbox/parser/20260829T1600Z: confirm every value the prior tickets'
checklists require is still alive after the KR0079 2025.2Q/2025.3Q item6 patch, plus a
whole-file item3=4+5+6+7 / item8=9+10+11+12 closure sweep (356 company-quarters).
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
d = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))


def val(code, item, q):
    for r in d:
        if r["원보험사코드"] == code and r["항목번호"] == item and r["공시분기"] == q:
            return r["값"]
    return "MISSING"


print("=== ticket checklist values (survival check) ===")
n_item32 = sum(1 for r in d if r["항목번호"] == 32)
print(f"항목32 cell count: {n_item32}  (expect 356)")
print(f"KR0083 2024.3Q item27: {val('KR0083', 27, '2024.3Q')}  (expect approx -265200 [-2,652억])")
print(f"KR0032 2026.2Q item6:  {val('KR0032', 6, '2026.2Q')}  (expect approx -10243 [-102억])")
print(f"KR0070 2024.4Q item6:  {val('KR0070', 6, '2024.4Q')}  (expect 586.0 [5.9억])")
print(f"KR0070 2025.1Q item6:  {val('KR0070', 6, '2025.1Q')}  (expect -3591.0 [-35.9억])")
print(f"KR0079 2026.2Q item6:  {val('KR0079', 6, '2026.2Q')}  (prior ticket, expect -18120.139965)")
print(f"KR0079 2026.2Q item11: {val('KR0079', 11, '2026.2Q')}  (held at 0)")

print("\n=== this ticket's new values ===")
print(f"KR0079 2025.2Q item6:  {val('KR0079', 6, '2025.2Q')}  (expect 7920.282929)")
print(f"KR0079 2025.2Q item7:  {val('KR0079', 7, '2025.2Q')}  (expect -6754.576523)")
print(f"KR0079 2025.3Q item6:  {val('KR0079', 6, '2025.3Q')}  (expect -2353.842208)")
print(f"KR0079 2025.3Q item7:  {val('KR0079', 7, '2025.3Q')}  (expect -9869.677728)")
print(f"KR0079 2025.2Q item11: {val('KR0079', 11, '2025.2Q')}  (held at 0)")
print(f"KR0079 2025.3Q item11: {val('KR0079', 11, '2025.3Q')}  (held at 0)")

print("\n=== full-file identity closure sweep (356 company-quarters expected) ===")
by_cq = {}
for r in d:
    by_cq.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]

n_cq = len(by_cq)
break3 = break8 = 0
tol = 0.01
breaks = []
for (code, q), items in by_cq.items():
    i3, i4, i5, i6, i7 = (items.get(k) for k in (3, 4, 5, 6, 7))
    if None not in (i3, i4, i5, i6, i7):
        if abs(i3 - (i4 + i5 + i6 + i7)) > tol:
            break3 += 1
            breaks.append(f"  BREAK item3=4+5+6+7: {code} {q}  {i3} vs {i4+i5+i6+i7}  "
                           f"resid={i3-(i4+i5+i6+i7):.6f}")
    i8, i9, i10, i11, i12 = (items.get(k) for k in (8, 9, 10, 11, 12))
    if None not in (i8, i9, i10, i11, i12):
        if abs(i8 - (i9 + i10 + i11 + i12)) > tol:
            break8 += 1
            breaks.append(f"  BREAK item8=9+10+11+12: {code} {q}  {i8} vs {i9+i10+i11+i12}  "
                           f"resid={i8-(i9+i10+i11+i12):.6f}")

for b in breaks:
    print(b)

print(f"\ncompany-quarters checked: {n_cq}  (expect 356)")
print(f"item3=4+5+6+7 breaks: {break3}")
print(f"item8=9+10+11+12 breaks: {break8}")
print(f"TOTAL closure breaks: {break3 + break8}")
