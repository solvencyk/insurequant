# -*- coding: utf-8 -*-
"""Read-only: dump current kics_disclosure.json state for group2's target buckets."""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGETS = [
    ("KR0002", "한화손해보험", ["2023.4Q","2024.1Q","2024.2Q","2024.4Q","2025.1Q","2025.2Q","2025.4Q","2026.1Q","2026.2Q"]),
    ("KR0003", "롯데손해보험", ["2026.1Q","2026.2Q"]),
    ("KR0049", "악사손해보험", ["2023.1Q","2023.2Q","2023.3Q","2024.3Q","2024.4Q","2025.1Q"]),
    ("KR0050", "하나손해보험", ["2023.3Q"]),
    ("KR0080", "에이아이에이생명보험", ["2024.1Q"]),
    ("KR0097", "하나생명보험", ["2024.4Q"]),
    ("KR0099", "KB라이프생명", ["2023.3Q","2023.4Q","2024.1Q","2025.1Q","2025.3Q"]),
    ("KR0104", "농협생명보험", ["2026.2Q"]),
    ("KR0150", "서울보증보험", ["2026.1Q"]),
    ("KR1098", "카카오페이손해보험", ["2024.4Q"]),
]

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    rows = json.load(f)
print(f"total rows: {len(rows)}")

idx = {}
for r in rows:
    key = (r["원보험사코드"], r["공시분기"], str(r["항목번호"]))
    idx[key] = r

for code, name, quarters in TARGETS:
    print(f"\n=== {code} {name} ===")
    for q in quarters:
        vals = []
        for item in (23,24,25,26):
            r = idx.get((code, q, str(item)))
            if r is None:
                vals.append(f"item{item}=ABSENT")
            else:
                vals.append(f"item{item}=(값={r.get('값')!r},후={r.get('값_적용후')!r})")
        print(f"  {q}: " + " | ".join(vals))
