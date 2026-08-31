import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", encoding="utf-8") as f:
    rows = json.load(f)

for q in ("2026.2Q", "2026.1Q", "2025.4Q"):
    print(f"--- KR0051 {q} items 1-23 ---")
    by_item = {r["항목번호"]: r for r in rows if r["원보험사코드"] == "KR0051" and r["공시분기"] == q}
    for i in range(1, 24):
        r = by_item.get(i)
        if r:
            print(f"  item{i}: {r['값']!r}  ({r['항목명']})")
        else:
            print(f"  item{i}: <ABSENT>")
