# -*- coding: utf-8 -*-
"""Fleet census: single-quarter (값_당분기) CSM identity open_q + new + int + adj + amort = close_q, per company-quarter, tol max(0.2%, 2억) like the YTD gate.
Does the gate see 2023.3Q Kyobo? Read-only."""
import json, subprocess, sys
from collections import defaultdict
def load(rev=None):
    if rev: return json.loads(subprocess.run(["git","show",f"{rev}:CSM_waterfall.json"],capture_output=True,check=True).stdout.decode("utf-8"))
    return json.load(open("CSM_waterfall.json", encoding="utf-8"))
def run(rows):
    d = defaultdict(dict)
    for r in rows: d[(r["원수사명"], r["공시분기"])][int(r["항목번호"])] = r["값_당분기"]
    fails = []; n = 0
    for k, m in sorted(d.items()):
        if any(m.get(i) is None for i in range(1, 7)): continue
        n += 1
        gap = m[1] + m[2] + m[3] + m[4] + m[5] - m[6]
        if abs(gap) > max(0.002 * abs(m[6]), 2.0): fails.append((k, round(gap, 2)))
    return n, fails
for label, rev in (("HEAD(now)", None), ("pre-commit 3e53aef8~1", "3e53aef8~1")):
    n, f = run(load(rev)); print(label, "checked", n, "fails", len(f)); [print("  ", x) for x in f[:40]]
