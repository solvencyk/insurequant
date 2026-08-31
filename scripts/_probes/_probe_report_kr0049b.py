# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_latest.json", "r", encoding="utf-8") as f:
    rep = json.load(f)

findings = rep["findings"]
print("total findings:", len(findings))
print("sample keys:", list(findings[0].keys()) if findings else None)

kr49 = [f for f in findings if f.get("code") == "KR0049" or f.get("원보험사코드") == "KR0049"]
print("KR0049 findings:", len(kr49))
if kr49:
    print("sample:", kr49[0])
