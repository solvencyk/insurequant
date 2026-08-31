# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

targets = list(range(36, 47)) + [53, 54]
seen = {}
for r in data:
    it = r["항목번호"]
    if it in targets and it not in seen:
        seen[it] = (r["항목명"], r["원보험사코드"], r["공시분기"])

for it in targets:
    if it in seen:
        label, code, q = seen[it]
        print(f"item{it}: {label!r}  (from {code} {q})")
    else:
        print(f"item{it}: NOT FOUND anywhere in master")

# also check: does ANY company have items 53/54 loaded at all?
c53 = sum(1 for r in data if r["항목번호"] == 53)
c54 = sum(1 for r in data if r["항목번호"] == 54)
print(f"\ntotal item53 rows in master: {c53}, item54 rows: {c54}")

# 2026.2Q KR0008 (already loaded this round per inbox) item36-40 for cross-check convention
print("\n--- KR0008 2026.2Q items 36-54 (if any) ---")
for r in sorted([r for r in data if r["원보험사코드"]=="KR0008" and r["공시분기"]=="2026.2Q" and 36<=r["항목번호"]<=54], key=lambda r:r["항목번호"]):
    print(f"  item{r['항목번호']} {r['항목명']!r} 값={r['값']!r} 후={r.get('값_적용후')!r}")
