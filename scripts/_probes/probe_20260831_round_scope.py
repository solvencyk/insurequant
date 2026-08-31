# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET_RULES = {"1","2","4","5","6","7","8","7_post","2_tier1_bridge","3_tier2_composition"}

with open("artifacts/kics_validation/report_latest.json", "r", encoding="utf-8") as f:
    report = json.load(f)

print("top-level keys:", list(report.keys()) if isinstance(report, dict) else type(report))

if isinstance(report, dict) and "findings" in report:
    findings = report["findings"]
elif isinstance(report, list):
    findings = report
else:
    # look for a list value
    findings = None
    for k, v in report.items():
        if isinstance(v, list) and v and isinstance(v[0], dict) and "rule" in v[0]:
            findings = v
            print("using key:", k)
            break

print("total findings:", len(findings))
if findings:
    print("sample keys:", list(findings[0].keys()))

reds = [f for f in findings if f.get("status") == "RED"]
print("total RED:", len(reds))

target_reds = [f for f in reds if str(f.get("rule")) in TARGET_RULES]
print("target-rule RED:", len(target_reds))

with open("scripts/_probes/_round_target_reds.json", "w", encoding="utf-8") as f:
    json.dump(target_reds, f, ensure_ascii=False, indent=2)

for r in sorted(target_reds, key=lambda x: (str(x.get("rule")), str(x.get("company")), str(x.get("period")))):
    print(r.get("rule"), "|", r.get("company"), "|", r.get("company_name", r.get("name","")), "|", r.get("period"), "|", "exp=", r.get("expected"), "act=", r.get("actual"), "diff=", r.get("diff"), "|", r.get("detail",""))
