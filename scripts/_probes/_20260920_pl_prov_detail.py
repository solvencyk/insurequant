#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drill into the back-trace result: hit/miss quality of the FS-API confirmation, and
which (company, quarter) fall back to the raw filing because no FS-API cache exists."""
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

res = json.loads((ROOT / "data/_derived/_probe_20260920_pl_prov_resolve.json")
                 .read_text(encoding="utf-8"))

fs = [e for e in res if e.get("resolution") == "FS_API_CONFIRMED"]
print(f"FS_API_CONFIRMED = {len(fs)}")
print("  hit histogram :", dict(sorted(Counter(e["fs_hit"] for e in fs).items())))
print("  miss histogram:", dict(sorted(Counter(e["fs_miss"] for e in fs).items())))
weak = [e for e in fs if e["fs_hit"] <= 2]
print(f"  cells confirmed by <=2 item matches = {len(weak)}")
for e in weak:
    print(f"    {e['company_code']} {e['quarter']} hit={e['fs_hit']} miss={e['fs_miss']} "
          f"nonnull={e['n_nonnull']}")
anymiss = [e for e in fs if e["fs_miss"]]
print(f"  cells with >=1 mismatching item (owner override / post-processing) = {len(anymiss)}")
for e in anymiss[:30]:
    print(f"    {e['company_code']} {e['quarter']} hit={e['fs_hit']} miss={e['fs_miss']}")

nofs = [e for e in res if e.get("resolution") == "RAW_HTML_NO_FS_CACHE"]
print(f"\nRAW_HTML_NO_FS_CACHE = {len(nofs)}")
print("  by quarter:", dict(sorted(Counter(e["quarter"] for e in nofs).items())))
byq = defaultdict(list)
for e in nofs:
    byq[e["quarter"]].append(e["company_code"])
for q in sorted(byq):
    print(f"   {q}: {len(byq[q])} companies")

print("\n  sample tried-paths (all absent on disk):")
for e in nofs[:3]:
    print(f"   {e['company_code']} {e['quarter']} -> {e.get('fs_api_tried')}")

multi = [e for e in res if len(e.get("raw_dirs_with_xml") or []) > 1]
print(f"\ncells whose (code,quarter) has >1 rcept dir carrying xml = {len(multi)}")
for e in multi:
    print(f"   {e['company_code']} {e['quarter']} {e['item_block']} -> {e['raw_dirs_with_xml']}")
