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

findings = data["findings"]

matched = []
for f_ in findings:
    rule = f_.get("rule")
    if rule not in RULES:
        continue
    code = f_.get("원보험사코드")
    q = f_.get("공시분기")
    if q != "2026.2Q":
        continue
    if code not in RULES[rule]:
        continue
    matched.append(f_)

print("total matched (any status):", len(matched))
red = [m for m in matched if m.get("status") == "RED"]
print("RED count:", len(red))

# group by rule
from collections import defaultdict
by_rule = defaultdict(list)
for m in red:
    by_rule[m["rule"]].append(m)

for rule, items in by_rule.items():
    print(f"\n=== {rule} ({len(items)}) ===")
    for it in sorted(items, key=lambda x: x["원보험사코드"]):
        print(f"  {it['원보험사코드']} {it['원수사명']} expected={it.get('expected')} actual={it.get('actual')} diff={it.get('diff')} detail={it.get('detail')}")

# Also print counts of expected 25 targets not found as RED (maybe GREEN/YELLOW/missing)
all_targets = []
for rule, codes in RULES.items():
    for c in codes:
        all_targets.append((rule, c))
print("\nTotal targets declared:", len(all_targets))

found_pairs = {(m["rule"], m["원보험사코드"]) for m in matched}
missing = [t for t in all_targets if t not in found_pairs]
print("targets with NO finding at all in report (any status):", missing)

status_map = {(m["rule"], m["원보험사코드"]): m["status"] for m in matched}
non_red = [(t, status_map.get(t)) for t in all_targets if status_map.get(t) != "RED"]
print("\ntargets NOT RED (status shown, None=no finding):")
for t, s in non_red:
    print(" ", t, s)
