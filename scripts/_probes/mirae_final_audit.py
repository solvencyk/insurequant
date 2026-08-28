"""Full closing audit requested by inbox/parser/20260828T2300Z before wrap-up: confirm the
specific values the ticket lists as "must still be alive" survived my KR0079 patch, plus a
whole-file item3=4+5+6+7 / item8=9+10+11+12 closure sweep (356 company-quarters).
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
d = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))


def val(code, item, q):
    for r in d:
        if r["원보험사코드"] == code and r["항목번호"] == item and r["공시분기"] == q:
            return r["값"]
    return "MISSING"


print("=== ticket checklist values ===")
n_item32 = sum(1 for r in d if r["항목번호"] == 32)
print(f"항목32 (기타 포괄손익 미분류) cell count: {n_item32}  (expect 356)")

print(f"KR0083 2024.3Q item27: {val('KR0083', 27, '2024.3Q')}  (expect approx -265200 [-2,652억])")
print(f"KR0032 2026.2Q item6:  {val('KR0032', 6, '2026.2Q')}  (expect approx -10243 [-102억])")
print(f"KR0032 2026.2Q item11: {val('KR0032', 11, '2026.2Q')}  (expect approx +4700 [+47억])")
print(f"KR0070 2024.4Q item6:  {val('KR0070', 6, '2024.4Q')}  (expect approx +590 [5.9억])")
print(f"KR0070 2025.1Q item6:  {val('KR0070', 6, '2025.1Q')}  (expect approx -3590 [-35.9억])")

print(f"\nKR0079 2026.2Q item6:  {val('KR0079', 6, '2026.2Q')}  (this ticket's new value)")
print(f"KR0079 2026.2Q item7:  {val('KR0079', 7, '2026.2Q')}")
print(f"KR0079 2026.2Q item11: {val('KR0079', 11, '2026.2Q')}  (held at 0, per ticket)")

print("\n=== full-file identity closure sweep (356 company-quarters expected) ===")
by_cq = {}
for r in d:
    by_cq.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]

n_cq = len(by_cq)
break3 = break8 = 0
tol = 0.01
for (code, q), items in by_cq.items():
    i3, i4, i5, i6, i7 = (items.get(k) for k in (3, 4, 5, 6, 7))
    if None not in (i3, i4, i5, i6, i7):
        if abs(i3 - (i4 + i5 + i6 + i7)) > tol:
            break3 += 1
            print(f"  BREAK item3=4+5+6+7: {code} {q}  {i3} vs {i4+i5+i6+i7}")
    i8, i9, i10, i11, i12 = (items.get(k) for k in (8, 9, 10, 11, 12))
    if None not in (i8, i9, i10, i11, i12):
        if abs(i8 - (i9 + i10 + i11 + i12)) > tol:
            break8 += 1
            print(f"  BREAK item8=9+10+11+12: {code} {q}  {i8} vs {i9+i10+i11+i12}")

print(f"\ncompany-quarters checked: {n_cq}")
print(f"item3=4+5+6+7 breaks: {break3}")
print(f"item8=9+10+11+12 breaks: {break8}")
print(f"TOTAL closure breaks: {break3 + break8}  (expect 0)")
