#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Who actually holds nonzero item8 (보증준비금) in the freshly-rebuilt IFRS17_BS.json,
broken down by 생손보여부? Confirms/refutes rule R-RSV-8's '생명보험 전용(16사)' premise
and checks whether any 손해보험 company (e.g. 서울보증보험, a guarantee-insurance
specialist) legitimately shows nonzero item8 -- read-only, for
inbox/parser/20260828T2350Z."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

rows = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
by_co = defaultdict(list)
biz = {}
for r in rows:
    if r["항목번호"] == 8:
        by_co[r["원보험사코드"]].append(r["값"])
        biz[r["원보험사코드"]] = (r["원수사명"], r["생손보여부"])

nonzero_holders = {co: vals for co, vals in by_co.items() if any(v for v in vals)}
zero_only = {co: vals for co, vals in by_co.items() if co not in nonzero_holders}

print(f"total companies with ANY item8 row: {len(by_co)}")
print(f"nonzero-holder companies: {len(nonzero_holders)}")
kinds = Counter(biz[co][1] for co in nonzero_holders)
print("  by 생손보여부:", dict(kinds))
for co in sorted(nonzero_holders):
    name, kind = biz[co]
    print(f"    {co} {name} ({kind}): n={len(nonzero_holders[co])} "
          f"max={max(nonzero_holders[co]):,.0f}")

print()
print(f"zero-only companies (all item8 rows == 0.0): {len(zero_only)}")
for co in sorted(zero_only):
    name, kind = biz[co]
    print(f"    {co} {name} ({kind}): n={len(zero_only[co])}")

# specific check: 서울보증보험 presence/value at all (any item, to confirm biz type + whether
# it has ANY item8 rows at all currently)
print()
name_hits = [co for co, (nm, kd) in biz.items() if "서울보증" in nm]
print("서울보증보험 in item8 series:", name_hits)
