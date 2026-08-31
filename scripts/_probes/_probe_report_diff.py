# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_20260831T051505Z.json", "r", encoding="utf-8") as f:
    before = json.load(f)
with open("artifacts/kics_validation/report_20260831T052933Z.json", "r", encoding="utf-8") as f:
    after = json.load(f)

def key(f):
    return (f["원보험사코드"], f["공시분기"], f["rule"])

before_map = {key(f): f["status"] for f in before["findings"]}
after_map = {key(f): f["status"] for f in after["findings"]}

all_keys = set(before_map) | set(after_map)
changed = [(k, before_map.get(k), after_map.get(k)) for k in all_keys if before_map.get(k) != after_map.get(k)]
changed.sort()
print(f"total changed findings: {len(changed)}")
for k, b, a in changed:
    print(f"  {k[0]} {k[1]} [{k[2]}]: {b} -> {a}")

print("\n=== KR0049 2026.2Q full finding set (after) ===")
kr49 = [f for f in after["findings"] if f.get("원보험사코드")=="KR0049" and f.get("공시분기")=="2026.2Q"
        and f["rule"] in ("47_tier2_census","47_tier2_census_post","48_tier2_limit","48_tier2_limit_post",
                          "2_tier1_bridge","2_tier1_bridge_post","3_tier2_composition","3_tier2_composition_post",
                          "50_tfi_tier_split","50_tfi_tier_split_post","51_tfi_tier2_composition","51_tfi_tier2_composition_post",
                          "53_tfi_memo_rows","53_tfi_memo_rows_post")]
for f in sorted(kr49, key=lambda x: x["rule"]):
    print(f"  [{f['status']:6s}] {f['rule']:28s} expected={f.get('expected')!r} actual={f.get('actual')!r} diff={f.get('diff')!r}")
    if f.get("detail"):
        print(f"           detail: {f['detail']}")
