# -*- coding: utf-8 -*-
import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", encoding="utf-8") as f:
    data = json.load(f)

code = "KR0075"
quarter = "2026.2Q"

rows = [r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == quarter]
rows.sort(key=lambda r: r.get("항목번호", 0))

out = []
for r in rows:
    out.append(r)

with open("scripts/_probes/_tmp_kr0075_rows.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"count={len(rows)}")
for r in rows:
    print(r.get("항목번호"), repr(r.get("항목명")), "값=", r.get("값"), "값_적용후=", r.get("값_적용후"))
