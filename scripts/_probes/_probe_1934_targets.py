import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_latest.json", encoding="utf-8") as f:
    d = json.load(f)

print("generated_at", d.get("generated_at"))

targets_19 = {"KR0004", "KR0011", "KR0029", "KR0051", "KR0068", "KR0080", "KR0087",
              "KR0094", "KR0099", "KR0100", "KR0104", "KR1098"}
targets_36 = {"KR0072", "KR1010"}

findings = d["findings"]
print("total findings", len(findings))
if findings:
    print("sample keys", list(findings[0].keys()))
    print("sample", findings[0])

print()
print("=== 19_market RED, all companies (for context) ===")
for row in findings:
    if row.get("rule") in ("19_market", "19", 19) and row.get("status") == "RED":
        print(row)

print()
print("=== 36_irr RED, all companies ===")
for row in findings:
    if row.get("rule") in ("36_irr", "36", 36) and row.get("status") == "RED":
        print(row)
