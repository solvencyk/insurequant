# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
with open("kics_disclosure.json", encoding="utf-8") as f:
    d = json.load(f)
r = d["records"] if isinstance(d, dict) and "records" in d else d
for code in ["KR0009","KR0150","KR0087"]:
    rows = [x for x in r if x.get("원보험사코드")==code and x.get("공시분기")=="2026.2Q" and x.get("항목번호") in (27,28)]
    for x in sorted(rows, key=lambda x: x["항목번호"]):
        print(code, x["항목번호"], x.get("값"), x.get("값_적용후"))
