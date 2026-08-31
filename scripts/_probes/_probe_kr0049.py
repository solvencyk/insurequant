# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0049"]
quarters = sorted(set(r.get("공시분기") for r in rows))
print("KR0049 quarters:", quarters)

for q in quarters:
    qrows = [r for r in rows if r.get("공시분기") == q]
    item_nos = sorted(set(r.get("항목번호") for r in qrows if r.get("항목번호") is not None and 47 <= r.get("항목번호") <= 54))
    print(f"\n=== {q} === items 47-54 present: {item_nos}")
    for r in sorted(qrows, key=lambda x: (x.get("항목번호") or 0)):
        if r.get("항목번호") is not None and 40 <= r["항목번호"] <= 54:
            print(f"  item{r['항목번호']:>3} {r.get('항목명','')!r:60s} 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
