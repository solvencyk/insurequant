# -*- coding: utf-8 -*-
import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", encoding="utf-8") as f:
    data = json.load(f)

code = "KR0075"

rows = [r for r in data if r.get("원보험사코드") == code and r.get("항목번호") in range(47, 55)]
rows.sort(key=lambda r: (r.get("공시분기", ""), r.get("항목번호", 0)))

for r in rows:
    print(r.get("공시분기"), r.get("항목번호"), repr(r.get("항목명")), "값=", r.get("값"), "값_적용후=", r.get("값_적용후"))
