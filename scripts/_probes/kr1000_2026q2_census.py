import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR1000"]
by_q = {}
for r in rows:
    by_q.setdefault(r["공시분기"], {})[r["항목번호"]] = r

for q in sorted(by_q.keys()):
    items = sorted(by_q[q].keys())
    print(f"{q}: n={len(items)} items={items}")

print()
print("=== 2026.1Q items 45-54 ===")
q1 = by_q.get("2026.1Q", {})
for i in range(45, 55):
    r = q1.get(i)
    if r:
        print(f"item{i}: 항목명={r['항목명']!r} 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
    else:
        print(f"item{i}: MISSING")

print()
print("=== 2026.2Q items 45-54 ===")
q2 = by_q.get("2026.2Q", {})
for i in range(45, 55):
    r = q2.get(i)
    if r:
        print(f"item{i}: 항목명={r['항목명']!r} 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
    else:
        print(f"item{i}: MISSING")

print()
print("=== 2025.4Q items 45-54 (one more quarter back for pattern check) ===")
q0 = by_q.get("2025.4Q", {})
for i in range(45, 55):
    r = q0.get(i)
    if r:
        print(f"item{i}: 항목명={r['항목명']!r} 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
    else:
        print(f"item{i}: MISSING")
