# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"C:\Users\sangwook.cho\Desktop\insurequant"
with open(ROOT + r"\kics_disclosure.json", "r", encoding="utf-8") as f:
    rows = json.load(f)
for r in rows:
    if r.get("원보험사코드") == "KR0029" and r.get("공시분기") in ("2025.3Q","2025.4Q") and r.get("항목번호") in (53,54):
        print(f"{r['공시분기']} item{r['항목번호']}: repr={r['항목명']!r} 값={r.get('값')!r}")
