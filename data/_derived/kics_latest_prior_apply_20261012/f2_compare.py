"""f2_compare.py BASE_TAG CAND_TAG -- compare two gate runs (gates/<tag>_slim.json): RED sets, every finding that moved, extra-axis and
registry signals, and whether any move falls outside the touched (code, quarter) buckets.  READ-ONLY."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
import harness as dryh  # noqa: E402

base = read_json(OUT / "gates" / f"{sys.argv[1]}_slim.json")
cand = read_json(OUT / "gates" / f"{sys.argv[2]}_slim.json")
touched = set()
for b in APPLIED:
    c, q = b.split("_")
    touched.add((c, q))
print("base", sys.argv[1], base["summary"], "rc", base["_rc"], "| cand", sys.argv[2], cand["summary"], "rc", cand["_rc"])
rb, rc_ = dryh.red_set(base), dryh.red_set(cand)
new_red = sorted(set(rc_) - set(rb))
gone_red = sorted(set(rb) - set(rc_))
same_red = sorted(set(rb) & set(rc_))
print(f"RED findings: base {len(rb)} -> cand {len(rc_)} | new {len(new_red)} | resolved {len(gone_red)} | unchanged {len(same_red)}")
for k in new_red:
    print("  NEW RED:", k, rc_[k])
for k in gone_red:
    print("  RESOLVED RED:", k, rb[k])
moved = dryh.finding_changes(base, cand)
print("findings that moved (status or numbers):", len(moved))
inside = [m for m in moved if tuple(m[0].split("|", 2)[:2]) in touched]
outside = [m for m in moved if tuple(m[0].split("|", 2)[:2]) not in touched]
print("   inside the 16 touched buckets:", len(inside), "| OUTSIDE:", len(outside))
for k, b, c in outside:
    print("   OUTSIDE:", k, b, "->", c)
# status transitions inside
from collections import Counter
tr = Counter()
for k, b, c in inside:
    tr[((b or ['-'])[0], (c or ['-'])[0])] += 1
print("   status transitions inside touched buckets:", dict(tr))
nx, gx = dryh.diff_extra(base, cand, "extra_red")
nr, gr = dryh.diff_extra(base, cand, "registry_red")
print("extra-axis RED new:", nx, "| gone:", gx)
print("registry-machinery signals new:", {k: len(v) for k, v in nr.items()}, "| gone:", {k: len(v) for k, v in gr.items()})
for k, v in nr.items():
    for x in v:
        print("   NEW registry:", k, x[:260])
print("census blocking missing:", base.get("census_blocking_missing"), "->", cand.get("census_blocking_missing"))
if "--detail" in sys.argv:
    for k, b, c in inside:
        print("   ", k, b, "->", c)
