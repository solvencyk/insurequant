import json, subprocess
from collections import defaultdict
def show(rev, f): return json.loads(subprocess.run(["git","show",f"{rev}:{f}"],capture_output=True,check=True).stdout.decode("utf-8"))
for f in ("CSM_waterfall.json","PL_breakdown.json"):
    a, b = show("3e53aef8~1", f), show("3e53aef8", f)
    ka = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r for r in a}
    by = defaultdict(lambda: defaultdict(set))
    for r in b:
        k = (r["원보험사코드"], r["공시분기"], str(r["항목번호"]))
        for fld in ("값", "값_당분기"):
            if ka[k].get(fld) != r.get(fld): by[r["공시분기"]][fld].add(k[2])
    print(f)
    for q in sorted(by): print("  ", q, {fld: len(v) for fld, v in by[q].items()})
    q4 = [q for q in by if q in ("2024.4Q",)]
    print("   2024.4Q changed:", bool(q4), "| quarters touched:", sorted(by))
