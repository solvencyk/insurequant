# -*- coding: utf-8 -*-
"""2026-09-01c: 시장위험 36-40 400/538 census.
- confirm denominator 538 = distinct (company,quarter) buckets in kics_disclosure.json (ANY item), not cadence-filtered
- split missing-item36 buckets by even/odd quarter
- confirm all 5 items (36-40) share the same missing-bucket set
- cross-check item19 (parent) presence/value for missing buckets
"""
import json
import io
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

idx = defaultdict(dict)
names = {}
for r in data:
    key = (r["원보험사코드"], r["공시분기"])
    idx[key][r["항목번호"]] = r.get("값")
    names[r["원보험사코드"]] = r["원수사명"]

print(f"total distinct (company,quarter) buckets = {len(idx)}")

qs = sorted({q for (_, q) in idx})
print(f"quarters present: {qs}")

even_keys = [k for k in idx if k[1].endswith(("2Q", "4Q"))]
odd_keys = [k for k in idx if not k[1].endswith(("2Q", "4Q"))]
print(f"even-Q buckets = {len(even_keys)}, odd-Q buckets = {len(odd_keys)}")

# missing sets per item
missing_sets = {}
for it in (36, 37, 38, 39, 40):
    missing_sets[it] = {k for k in idx if idx[k].get(it) is None}
    print(f"item{it}: missing = {len(missing_sets[it])}")

# are all 5 the same set?
allsame = all(missing_sets[36] == missing_sets[it] for it in (37, 38, 39, 40))
print(f"all 5 items share identical missing-bucket set: {allsame}")
if not allsame:
    for it in (37, 38, 39, 40):
        diff = missing_sets[36] ^ missing_sets[it]
        if diff:
            print(f"  diff item36 vs item{it}: {sorted(diff)[:10]} ... ({len(diff)} total)")

miss36 = missing_sets[36]
miss36_even = {k for k in miss36 if k[1].endswith(("2Q", "4Q"))}
miss36_odd = {k for k in miss36 if not k[1].endswith(("2Q", "4Q"))}
print(f"\nitem36 missing: even-Q={len(miss36_even)}, odd-Q={len(miss36_odd)}")

# odd-Q buckets where item36 IS present (disclosed exceptions like 카카오 2023.3Q)
odd_present36 = {k for k in odd_keys if idx[k].get(36) is not None}
print(f"odd-Q buckets where item36 IS present (exceptions): {len(odd_present36)}")
for k in sorted(odd_present36):
    print(f"    EXCEPTION-DISCLOSED-ODD: {names[k[0]]}({k[0]}) {k[1]} item36={idx[k].get(36)}")

# among even-Q missing, check item19 (parent) presence/value
print(f"\n--- even-Q missing item36: item19(parent) cross-check ---")
zero_parent = 0
none_parent = 0
nonzero_parent = 0
for k in sorted(miss36_even):
    v19 = idx[k].get(19)
    if v19 is None:
        none_parent += 1
        tag = "PARENT_NONE"
    elif v19 == 0:
        zero_parent += 1
        tag = "PARENT_ZERO"
    else:
        nonzero_parent += 1
        tag = "PARENT_NONZERO_GAP"
    print(f"    {tag}: {names[k[0]]}({k[0]}) {k[1]} item19={v19}")
print(f"\nsummary even-Q missing36: parent_none={none_parent} parent_zero={zero_parent} parent_nonzero_gap={nonzero_parent} total={len(miss36_even)}")

# among odd-Q missing (excluding disclosed exceptions), just count by company for reference
print(f"\n--- odd-Q missing item36 (expected-absent by cadence unless exception) ---")
by_company = defaultdict(list)
for k in sorted(miss36_odd):
    by_company[k[0]].append(k[1])
print(f"odd-Q missing spans {len(by_company)} companies")
