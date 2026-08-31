import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", encoding="utf-8") as f:
    rows = json.load(f)

targets_19 = ["KR0004", "KR0011", "KR0029", "KR0051", "KR0068", "KR0080", "KR0087",
              "KR0094", "KR0099", "KR0100", "KR0104", "KR1098"]
targets_36 = ["KR0072", "KR1010"]

by_code_q = {}
for r in rows:
    key = (r["원보험사코드"], r["공시분기"])
    by_code_q.setdefault(key, []).append(r)

def show(code, quarter, items):
    key = (code, quarter)
    rs = by_code_q.get(key, [])
    by_item = {r["항목번호"]: r for r in rs}
    name = rs[0]["원수사명"] if rs else "?"
    print(f"--- {code} {name} {quarter} ---")
    for it in items:
        r = by_item.get(it)
        if r is None:
            print(f"  item{it}: <ABSENT>")
        else:
            print(f"  item{it}: 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r} 항목명={r.get('항목명')!r}")

print("=========== 19_market targets (2026.2Q) ===========")
for code in targets_19:
    show(code, "2026.2Q", [15, 19] + list(range(36, 41)))
    print()

print("=========== 19_market targets (2026.1Q ref, for item-label copy) ===========")
for code in targets_19:
    show(code, "2026.1Q", [19] + list(range(36, 41)))
    print()

print("=========== 36_irr targets (2026.2Q) ===========")
for code in targets_36:
    show(code, "2026.2Q", [19, 36] + list(range(41, 47)))
    print()

print("=========== 36_irr targets (2026.1Q ref) ===========")
for code in targets_36:
    show(code, "2026.1Q", [36] + list(range(41, 47)))
    print()

print("=========== KR0029 AIG 2025.4Q ref (adjacent even-Q, for label copy) ===========")
show("KR0029", "2025.4Q", [19] + list(range(36, 41)))
