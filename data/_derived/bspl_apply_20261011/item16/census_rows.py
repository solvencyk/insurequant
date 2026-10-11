import json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
pl = json.load(open("PL_breakdown.json", encoding="utf-8"))
codes = sys.argv[1].split(",")
items = [int(x) for x in sys.argv[2].split(",")]
d = defaultdict(dict)
for r in pl:
    if r["원보험사코드"] in codes and r["항목번호"] in items:
        d[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = (r["값"], r["값_당분기"])
qs = sorted({q for v in d.values() for q in v})
for k in sorted(d):
    print(k)
    print("  " + " ".join(f"{q}:{d[k][q][0]}/{d[k][q][1]}" if q in d[k] else f"{q}:ABSENT" for q in qs))
