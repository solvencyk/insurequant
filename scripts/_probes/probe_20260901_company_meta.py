# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)
records = data["records"] if isinstance(data, dict) and "records" in data else data

targets = ["KR0150", "KR0087", "KR0083", "KR1011", "KR0051"]
for code in targets:
    rows = [r for r in records if r.get("원보험사코드") == code]
    if rows:
        r = rows[0]
        print(code, "|", r.get("원수사명"), "|", r.get("티커"), "|", r.get("생손보여부"))
