import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(".")
TARGET_RULES = {"53_tfi_memo_rows", "47_tier2_census", "47_tier2_census_post",
                 "50_tfi_tier_split", "50_tfi_tier_split_post"}

# original 25 (code, rule) pairs from report_latest.json BEFORE my patch (already saved earlier)
ORIGINAL_25 = {
    ("KR0001", "47_tier2_census"), ("KR0004", "47_tier2_census"), ("KR0083", "47_tier2_census"),
    ("KR0087", "47_tier2_census"), ("KR0094", "47_tier2_census"), ("KR1011", "47_tier2_census"),
    ("KR1098", "47_tier2_census"),
    ("KR0001", "47_tier2_census_post"), ("KR0003", "47_tier2_census_post"),
    ("KR0011", "47_tier2_census_post"), ("KR0029", "47_tier2_census_post"),
    ("KR0083", "47_tier2_census_post"), ("KR0104", "47_tier2_census_post"),
    ("KR1098", "47_tier2_census_post"),
    ("KR1098", "50_tfi_tier_split"), ("KR1098", "50_tfi_tier_split_post"),
    ("KR0003", "53_tfi_memo_rows"), ("KR0011", "53_tfi_memo_rows"), ("KR0051", "53_tfi_memo_rows"),
    ("KR0070", "53_tfi_memo_rows"), ("KR0072", "53_tfi_memo_rows"), ("KR0080", "53_tfi_memo_rows"),
    ("KR0082", "53_tfi_memo_rows"), ("KR0097", "53_tfi_memo_rows"), ("KR0100", "53_tfi_memo_rows"),
}

# find the most recent report file
import glob
reports = sorted(glob.glob("artifacts/kics_validation/report_2*.json"))
latest = reports[-1]
print("using report:", latest)
data = json.load(open(latest, encoding="utf-8"))
findings = data["findings"]

now_red = []
for f in findings:
    if f.get("rule") in TARGET_RULES and f.get("status") == "RED":
        now_red.append(f)

print(f"total RED in target rules now: {len(now_red)}")
now_red_pairs_2026q2 = set()
other_quarter = []
for f in now_red:
    code = f.get("원보험사코드")
    q = f.get("공시분기")
    rule = f.get("rule")
    if q == "2026.2Q":
        now_red_pairs_2026q2.add((code, rule))
    else:
        other_quarter.append(f)

print(f"\n2026.2Q RED count: {len(now_red_pairs_2026q2)}")
resolved = ORIGINAL_25 - now_red_pairs_2026q2
still_red = ORIGINAL_25 & now_red_pairs_2026q2
new_red = now_red_pairs_2026q2 - ORIGINAL_25
print(f"resolved: {len(resolved)}")
for r in sorted(resolved):
    print("  RESOLVED", r)
print(f"still RED (in my original 25): {len(still_red)}")
for r in sorted(still_red):
    print("  STILL-RED", r)
print(f"NEW red not in original 25 (2026.2Q, target rules): {len(new_red)}")
for r in sorted(new_red):
    print("  NEW-RED", r)

print(f"\nother-quarter RED in target rules (pre-existing, not mine, count={len(other_quarter)}):")
by_q = {}
for f in other_quarter:
    by_q.setdefault(f.get("공시분기"), 0)
    by_q[f.get("공시분기")] += 1
for q, c in sorted(by_q.items()):
    print(f"  {q}: {c}")

# print full detail for still-red and new-red for diagnosis
print("\n--- FULL DETAIL: still-red + new-red ---")
for f in now_red:
    key = (f.get("원보험사코드"), f.get("rule"))
    if f.get("공시분기") == "2026.2Q" and (key in still_red or key in new_red):
        print("="*80)
        for k in ("rule","원보험사코드","원수사명","공시분기","status","expected","actual"):
            print(f"  {k}: {f.get(k)}")
        print(f"  detail: {f.get('detail')}")
