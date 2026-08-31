# -*- coding: utf-8 -*-
import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", encoding="utf-8") as f:
    data = json.load(f)

code = "KR0075"

rows = [r for r in data if r.get("원보험사코드") == code and r.get("항목번호") in (1, 47, 48, 49, 52)]
rows.sort(key=lambda r: (r.get("공시분기", ""), r.get("항목번호", 0)))

for r in rows:
    v = r.get("값")
    vp = r.get("값_적용후")
    print(r.get("공시분기"), r.get("항목번호"), "값:", type(v).__name__, repr(v),
          "| 값_적용후:", type(vp).__name__, repr(vp))
    # also dump the 항목명 raw bytes as hex to check for hidden chars
    name = r.get("항목명")
    print("   항목명 repr:", repr(name))
