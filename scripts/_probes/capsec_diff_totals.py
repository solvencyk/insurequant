# -*- coding: utf-8 -*-
"""Compare total_hybrid_outstanding_mn / total_subordinated_outstanding_mn per company between
two snapshots -- these are SUMS over all bonds, so they catch amount drift regardless of any
per-bond key-matching ambiguity (duplicate issue dates etc)."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
before = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
after = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
b_by_code = {c["code"]: c for c in before["companies"]}
a_by_code = {c["code"]: c for c in after["companies"]}

diffs = 0
for code in sorted(b_by_code):
    b, a = b_by_code[code], a_by_code[code]
    bh, ah = b["total_hybrid_outstanding_mn"], a["total_hybrid_outstanding_mn"]
    bs, asx = b["total_subordinated_outstanding_mn"], a["total_subordinated_outstanding_mn"]
    if bh != ah or bs != asx:
        diffs += 1
        print(f"{code}: hybrid {bh} -> {ah} (delta {ah - bh})   sub {bs} -> {asx} (delta {asx - bs})")
print(f"\ncompanies with total-amount delta: {diffs} / {len(b_by_code)}")
