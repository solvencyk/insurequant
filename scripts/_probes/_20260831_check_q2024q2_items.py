# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
rows = [r for r in data if r.get("원보험사코드") == "KR0029" and r.get("공시분기") == "2024.2Q"]
print(f"KR0029 2024.2Q: {len(rows)} rows, items={sorted(r['항목번호'] for r in rows)}")
for r in sorted(rows, key=lambda x: x["항목번호"]):
    if 27 <= r["항목번호"] <= 46:
        print(f"  item{r['항목번호']} {r['항목명']}: 값={r.get('값')}")
