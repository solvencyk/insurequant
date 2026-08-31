import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET_RULES = {
    "53_tfi_memo_rows": ["KR0003", "KR0011", "KR0051", "KR0070", "KR0072", "KR0080", "KR0082", "KR0097", "KR0100"],
    "47_tier2_census": ["KR0001", "KR0004", "KR0083", "KR0087", "KR0094", "KR1011", "KR1098"],
    "47_tier2_census_post": ["KR0001", "KR0003", "KR0011", "KR0029", "KR0083", "KR0104", "KR1098"],
    "50_tfi_tier_split": ["KR1098"],
    "50_tfi_tier_split_post": ["KR1098"],
}

data = json.load(open("artifacts/kics_validation/report_latest.json", encoding="utf-8"))
findings = data["findings"]
print("total findings:", len(findings))
print("generated_at:", data.get("generated_at"))

rows = []
for f in findings:
    rule = f.get("rule")
    if rule not in TARGET_RULES:
        continue
    code = f.get("원보험사코드") or f.get("code")
    q = f.get("공시분기") or f.get("quarter")
    status = f.get("status")
    if status != "RED":
        continue
    if q != "2026.2Q":
        continue
    rows.append(f)

print("RED count in target rules @2026.2Q:", len(rows))
print()
for f in sorted(rows, key=lambda x: (x.get("rule",""), x.get("원보험사코드",""))):
    print("="*100)
    for k in ("rule", "원보험사코드", "원수사명", "공시분기", "status", "expected", "actual", "diff"):
        print(f"  {k}: {f.get(k)}")
    print(f"  detail: {f.get('detail')}")
