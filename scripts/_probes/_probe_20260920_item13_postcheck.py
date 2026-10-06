# -*- coding: utf-8 -*-
"""Independent post-hoc verification of the item13 revert: backup vs live master."""
import json, io, os, sys
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIVE = os.path.join(REPO, "kics_disclosure.json")
BAK = sys.argv[1]

def key(r):
    return (r["원보험사코드"], r["공시분기"], int(r["항목번호"]))

a = {key(r): r for r in json.load(io.open(BAK, encoding="utf-8"))}
b = {key(r): r for r in json.load(io.open(LIVE, encoding="utf-8"))}
print("rows before=%d after=%d  keys_added=%d keys_removed=%d"
      % (len(a), len(b), len(set(b) - set(a)), len(set(a) - set(b))))
diff = [k for k in a if k in b and a[k] != b[k]]
print("rows differing: %d" % len(diff))
print("by item:", dict(Counter(k[2] for k in diff)))
bad = []
for k in diff:
    ra, rb = dict(a[k]), dict(b[k])
    if "값_적용후" not in ra or "값_적용후" in rb:
        bad.append((k, "not a pure 값_적용후 removal"))
        continue
    ra.pop("값_적용후")
    if ra != rb:
        bad.append((k, "other fields changed"))
print("violations:", bad if bad else "none")
# item4/item12 untouched?
for it in (4, 12):
    ch = [k for k in diff if k[2] == it]
    print("item%d changed rows: %d" % (it, len(ch)))
# remaining mirrored item13 with 값_적용후
rem = sum(1 for k, r in b.items() if k[2] == 13 and r.get("값_적용후") is not None)
print("item13 rows still carrying 값_적용후: %d (was %d)"
      % (rem, sum(1 for k, r in a.items() if k[2] == 13 and r.get("값_적용후") is not None)))
