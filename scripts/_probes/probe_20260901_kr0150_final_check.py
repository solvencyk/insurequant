# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
with open("kics_disclosure.json", encoding="utf-8") as f:
    d = json.load(f)
r = d["records"] if isinstance(d, dict) and "records" in d else d
rows = [x for x in r if x.get("원보험사코드")=="KR0150" and x.get("공시분기")=="2026.2Q"]
print("KR0150 2026.2Q rows:", len(rows))
print(sorted(x["항목번호"] for x in rows))
