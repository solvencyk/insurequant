import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CODES = ["KR0001", "KR0003", "KR0004", "KR0011", "KR0029", "KR0051", "KR0070",
         "KR0072", "KR0080", "KR0082", "KR0083", "KR0087", "KR0094", "KR0097",
         "KR0100", "KR0104", "KR1011", "KR1098"]
ITEMS = [1, 2, 3, 14, 47, 48, 49, 50, 51, 52, 53, 54]

data = json.load(open("kics_disclosure.json", encoding="utf-8"))
by_code_q = {}
for row in data:
    if row.get("공시분기") != "2026.2Q":
        continue
    code = row.get("원보험사코드")
    if code not in CODES:
        continue
    item = row.get("항목번호")
    if item not in ITEMS:
        continue
    by_code_q.setdefault(code, {})[item] = (row.get("값"), row.get("값_적용후"), row.get("항목명"))

for code in CODES:
    print("=" * 90)
    print(code)
    d = by_code_q.get(code, {})
    for item in ITEMS:
        if item in d:
            v, vp, label = d[item]
            print(f"  item{item:2d} ({label}): 값={v!r}  값_적용후={vp!r}")
        else:
            print(f"  item{item:2d}: <NOT IN MASTER>")
