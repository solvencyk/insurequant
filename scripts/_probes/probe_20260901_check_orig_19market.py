# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET_COMPANIES = {"KR0009","KR0150","KR0087","KR0083","KR1011","KR0051","KR0079"}

with open("artifacts/kics_validation/report_20260831T123422Z.json", "r", encoding="utf-8") as f:
    report = json.load(f)
findings = report["findings"]

for f in findings:
    if f.get("원보험사코드") in TARGET_COMPANIES and f.get("공시분기")=="2026.2Q" and str(f.get("rule")) in ("19_market","36_irr","8_post"):
        print(f.get('원보험사코드'), f.get('rule'), f.get('status'), '| exp=',f.get('expected'),'act=',f.get('actual'),'|', (f.get('detail') or '')[:100])
