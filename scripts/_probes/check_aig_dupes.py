# -*- coding: utf-8 -*-
import io, json, sys
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"C:\Users\sangwook.cho\Desktop\insurequant"
with open(ROOT + r"\kics_disclosure.json", "r", encoding="utf-8") as f:
    rows = json.load(f)

code = "KR0029"
combo_counter = Counter()
for r in rows:
    if r.get("원보험사코드") == code:
        combo_counter[(r.get("공시분기"), r.get("항목번호"))] += 1

dupes = {k: v for k, v in combo_counter.items() if v > 1}
print(f"AIG(KR0029) total rows: {sum(1 for r in rows if r.get('원보험사코드')==code)}")
print(f"duplicate (quarter,item) combos: {len(dupes)}")
for k, v in sorted(dupes.items()):
    print(f"  {k}: {v} rows")
    for r in rows:
        if r.get("원보험사코드")==code and r.get("공시분기")==k[0] and r.get("항목번호")==k[1]:
            print(f"    값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r} 항목명={r.get('항목명')!r}")

# also confirm target quarters items 2025.2Q/2025.3Q are single-instance
print()
print("2025.2Q / 2025.3Q specific item37 double-check:")
for r in rows:
    if r.get("원보험사코드")==code and r.get("공시분기") in ("2025.2Q","2025.3Q") and r.get("항목번호") in (37,38,39,40,47,49,50,51,28):
        print(f"  {r.get('공시분기')} item{r.get('항목번호')} 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
