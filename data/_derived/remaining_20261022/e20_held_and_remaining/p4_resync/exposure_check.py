# -*- coding: utf-8 -*-
"""Read-only: which of the changed PL_breakdown cells (HEAD~1 -> HEAD) does the site actually show?
IFRS17.html Panel 3 (fetches PL_breakdown.json): year mode = field 값 at every 4Q + the latest quarter (if not 4Q); quarter mode = field 값_당분기 for the last 5 quarters (asc slice(-5)).
Waterfall chart = latest quarter only (plPeriod).  compare.html = panel_compare.json, latest as-of with fallback only when the company has no later value."""
import json, subprocess
from collections import defaultdict, Counter
old = json.loads(subprocess.check_output(["git", "show", "HEAD~1:PL_breakdown.json"]).decode("utf-8"))
new = json.load(open("PL_breakdown.json", encoding="utf-8"))
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
o = {key(r): r for r in old}
quarters = defaultdict(set)
for r in new:
    quarters[r["원보험사코드"]].add(r["공시분기"])
def qk(q): return (int(q[:4]), int(q[5]))
shown_year = shown_q = 0
res = Counter(); rows = []
for r in new:
    k = key(r); p = o.get(k)
    if p is None: continue
    for f in ("값", "값_당분기"):
        if p.get(f) != r.get(f):
            code, item, q = k
            qs = sorted(quarters[code], key=qk)
            latest = qs[-1]
            if f == "값":
                vis_tbl = q.endswith("4Q") or q == latest
                vis_chart = q == latest
                where = "IFRS17.html 연도모드 표" if vis_tbl else ""
            else:
                vis_tbl = q in qs[-5:]
                vis_chart = q == latest
                where = "IFRS17.html 분기모드 표" if vis_tbl else ""
            res[(f, bool(vis_tbl))] += 1
            rows.append((code, r["원수사명"], q, item, f, p.get(f), r.get(f), where, latest))
print("changed cells:", len(rows))
for (f, v), n in sorted(res.items()): print(f"  field {f}: shown_in_IFRS17_table={v}: {n}")
print("--- shown cells (company, quarter, item, field, old->new, latest)")
for x in sorted(rows):
    if x[7]: print("  ", x[0], x[1], x[2], "item", x[3], x[4], x[5], "->", x[6], "|", x[7], "| latest", x[8])
print("--- by company/quarter latest")
print({c: sorted(quarters[c], key=qk)[-1] for c in sorted({x[0] for x in rows})})
print("--- cells in 2023.1Q/2023.2Q:", sorted({(x[0], x[2]) for x in rows if x[2] in ("2023.1Q", "2023.2Q")}))
print("--- of which shown in IFRS17.html tables:", [x for x in rows if x[2] in ("2023.1Q", "2023.2Q") and x[7]])
