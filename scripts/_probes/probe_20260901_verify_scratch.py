# -*- coding: utf-8 -*-
import json, sys, io, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET_RULES = {"1","2","4","5","6","7","8","7_post","2_tier1_bridge","3_tier2_composition"}
TARGET_COMPANIES = {"KR0009","KR0150","KR0087","KR0083","KR1011","KR0051","KR0079"}

# pick latest report
reports = sorted(glob.glob("artifacts/kics_validation/report_2026*.json"), key=os.path.getmtime)
latest = reports[-1]
print("using report:", latest)

with open(latest, "r", encoding="utf-8") as f:
    report = json.load(f)

findings = report["findings"]
reds = [f for f in findings if f.get("status") == "RED"]
target_reds = [f for f in reds if str(f.get("rule")) in TARGET_RULES]
print("total RED:", len(reds), " target-rule RED:", len(target_reds))
print()
rows = sorted(target_reds, key=lambda x: (str(x.get("rule")), str(x.get("원보험사코드")), str(x.get("공시분기"))))
for r in rows:
    print(f"{r.get('rule'):22s} | {r.get('원보험사코드')} {r.get('원수사명')} | {r.get('공시분기')} | exp={r.get('expected')} act={r.get('actual')} diff={r.get('diff')} | {r.get('detail','')[:90]}")

print()
print("=== 2026.2Q-only target-rule RED (my round-23 scope) ===")
my_scope = [r for r in target_reds if r.get("공시분기") == "2026.2Q"]
print(len(my_scope), "remaining")
for r in my_scope:
    print(f"{r.get('rule'):22s} | {r.get('원보험사코드')} {r.get('원수사명')} | exp={r.get('expected')} act={r.get('actual')} diff={r.get('diff')} | {r.get('detail','')[:120]}")

# also check for any NEW red in companies I touched, any rule, any quarter
print()
print("=== ALL RED for my 7 companies (any rule/quarter) ===")
company_reds = [f for f in reds if f.get("원보험사코드") in TARGET_COMPANIES]
for r in sorted(company_reds, key=lambda x: (str(x.get("원보험사코드")), str(x.get("공시분기")), str(x.get("rule")))):
    print(f"{r.get('원보험사코드')} {r.get('공시분기'):>8s} | {r.get('rule'):25s} | exp={r.get('expected')} act={r.get('actual')} diff={r.get('diff')} | {r.get('detail','')[:80]}")
