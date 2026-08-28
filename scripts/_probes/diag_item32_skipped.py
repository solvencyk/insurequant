"""For the 61 'skipped' (missing-term) cells from validate_item32_full_universe.py, check
whether items 26-30 are ALSO missing in a FRESH tier1_for() call (genuine source gap) or only
missing in the (possibly stale) PL_breakdown.json master (extraction gap worth flagging, but
out of THIS ticket's scope -- item32 only)."""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import resolve_corp, tier1_for  # noqa: E402

d = json.load(open("PL_breakdown.json", encoding="utf-8"))
by_cq = defaultdict(dict)
name_by_code = {}
for r in d:
    key = (r["원보험사코드"], r["공시분기"])
    by_cq[key][r["항목번호"]] = r["값"]
    name_by_code[r["원보험사코드"]] = r["원수사명"]

targets = [(code, q) for (code, q), items in by_cq.items() if 25 in items and items[25] is not None]

mismatch = []   # master has None, fresh t1 has a value -> master staleness
genuine_gap = []  # both None -> real source gap
for code, q in sorted(targets):
    name = name_by_code[code]
    items = by_cq[(code, q)]
    missing_master = [k for k in (26, 27, 28, 29, 30) if items.get(k) is None]
    if not missing_master:
        continue
    cc = resolve_corp(name)
    t1 = tier1_for(name, q, code) if cc else None
    for k in missing_master:
        fresh_v = (t1 or {}).get(k)
        if fresh_v is not None:
            mismatch.append((code, name, q, k, fresh_v, items.get(25)))
        else:
            genuine_gap.append((code, name, q, k))

print(f"master-stale (fresh has a value, master doesn't): {len(mismatch)}")
for row in mismatch:
    print(f"   {row}")
print(f"\ngenuine gap (both master and fresh None): {len(genuine_gap)}")
by_code = defaultdict(lambda: defaultdict(int))
for code, name, q, k in genuine_gap:
    by_code[(code, name)][k] += 1
for (code, name), ks in sorted(by_code.items()):
    print(f"   {code} {name}: {dict(ks)}")
