# -*- coding: utf-8 -*-
"""Read-only: list the PL_breakdown cells visible in IFRS17.html (year mode 4Q+latest via 값; quarter mode last 5 quarters via 값_당분기) with old/new/pct."""
import json, subprocess
from collections import defaultdict
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
old = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads(subprocess.check_output(["git", "-C", ROOT, "show", "77bcc10d:PL_breakdown.json"]).decode("utf-8"))}
new_rows = json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))
qk = lambda q: (int(q[:4]), int(q[5]))
qs = defaultdict(set)
for r in new_rows: qs[r["원보험사코드"]].add(r["공시분기"])
out = []
for r in new_rows:
    k = (r["원보험사코드"], r["항목번호"], r["공시분기"]); p = old.get(k)
    if p is None: continue
    s = sorted(qs[k[0]], key=qk); latest = s[-1]
    year = {q for q in s if q.endswith("4Q")} | {latest}; last5 = set(s[-5:])
    for f in ("값", "값_당분기"):
        a, b = p.get(f), r.get(f)
        if a == b: continue
        vis = (k[2] in year) if f == "값" else (k[2] in last5)
        if vis:
            try: pct = (float(b) - float(a)) / abs(float(a)) * 100 if a not in (None, 0, "0") else None
            except Exception: pct = None
            out.append((r["원수사명"], k[2], k[1], r["항목명"], f, a, b, pct))
for o in sorted(out, key=lambda t: (t[0], qk(t[1]), t[2], t[4])):
    pc = "n/a" if o[7] is None else f"{o[7]:+.1f}%"
    print(f"{o[0]} {o[1]} #{o[2]} {o[3]} [{o[4]}]: {o[5]} -> {o[6]} ({pc})")
print("visible cells:", len(out), "| >1%:", sum(1 for o in out if o[7] is None or abs(o[7]) > 1))
