import json
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

RULES = {
    "53_tfi_memo_rows": {"KR0003","KR0011","KR0051","KR0070","KR0072","KR0080","KR0082","KR0097","KR0100"},
    "47_tier2_census": {"KR0001","KR0004","KR0083","KR0087","KR0094","KR1011","KR1098"},
    "47_tier2_census_post": {"KR0001","KR0003","KR0011","KR0029","KR0083","KR0104","KR1098"},
    "50_tfi_tier_split": {"KR1098"},
    "50_tfi_tier_split_post": {"KR1098"},
}

with open("artifacts/kics_validation/report_latest.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(type(data), len(data) if hasattr(data, "__len__") else "")
if isinstance(data, dict):
    print("TOP KEYS:", list(data.keys())[:20])
