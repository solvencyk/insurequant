import json
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_latest.json", "r", encoding="utf-8") as f:
    data = json.load(f)

findings = data["findings"]
print("findings type:", type(findings), len(findings))
if isinstance(findings, list):
    print("sample:", json.dumps(findings[0], ensure_ascii=False, indent=2)[:2000])
elif isinstance(findings, dict):
    print("keys sample:", list(findings.keys())[:10])
