# -*- coding: utf-8 -*-
"""Read-only: distribution of 공시분기 in CSM_amortization.json, 9/10-year coverage, and a sanity check of every
(company, 4Q) schedule against the closing CSM of the same quarter and of the previous year-end (pre-existing defect scan)."""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")

am = json.loads((ROOT / "CSM_amortization.json").read_text(encoding="utf-8"))
print("rows", len(am))
print("quarters:", sorted(collections.Counter(r["공시분기"] for r in am).items()))
by = collections.defaultdict(dict)
for r in am:
    by[(r["원보험사코드"], r["공시분기"])][r["경과차년"]] = r["상각액"]
print("company-quarters", len(by))
nn = collections.Counter(sum(1 for v in d.values() if v is not None) for d in by.values())
print("non-null buckets per company-quarter:", sorted(nn.items()))

wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
close = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in wf if r["항목번호"] == 6}
name = {r["원보험사코드"]: r["원수사명"] for r in wf}
print("\ncompany 4Q: sum(1..10y buckets) | closing CSM(N) | closing CSM(N-1) | sum/close(N) | sum/close(N-1)")
for (code, q), d in sorted(by.items()):
    s = sum(v for v in d.values() if v is not None)
    y = int(q[:4])
    cN = close.get((code, q))
    cP = close.get((code, f"{y - 1}.4Q"))
    n = sum(1 for v in d.values() if v is not None)
    rN = None if not cN else round(s / cN, 3)
    rP = None if not cP else round(s / cP, 3)
    print(f"  {code} {name.get(code, ''):<12s} {q} n={n:>2d} sum={s:>12.1f} closeN={cN} closeN-1={cP}  ratioN={rN} ratioN-1={rP}")
