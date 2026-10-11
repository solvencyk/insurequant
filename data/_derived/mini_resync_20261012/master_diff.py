# -*- coding: utf-8 -*-
"""Diff masters between a baseline commit and the working tree: python master_diff.py <baseline_commit>."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
base = sys.argv[1]
SPEC = {
    "PL_breakdown.json": ["원보험사코드", "항목번호", "공시분기"],
    "IFRS17_BS.json": ["원보험사코드", "항목번호", "공시분기"],
    "CSM_waterfall.json": ["원보험사코드", "항목번호", "공시분기"],
    "CSM_amortization.json": ["원보험사코드", "공시분기", "경과차년"],
    "CSM_sensitivity.json": ["원보험사코드", "공시분기", "순번"],
    "insurance_liability_portfolio.json": ["원보험사코드", "항목번호", "공시분기"],
}
for f, key in SPEC.items():
    old = json.loads(subprocess.run(["git", "show", f"{base}:{f}"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
    new = json.loads((ROOT / f).read_text(encoding="utf-8"))
    ko = {tuple(r.get(k) for k in key): r for r in old}
    kn = {tuple(r.get(k) for k in key): r for r in new}
    assert len(ko) == len(old) and len(kn) == len(new), (f, "dup keys")
    added = sorted(set(kn) - set(ko), key=str)
    removed = sorted(set(ko) - set(kn), key=str)
    changed = {}
    for k in set(ko) & set(kn):
        a, b = ko[k], kn[k]
        for c in set(a) | set(b):
            if a.get(c) != b.get(c):
                changed.setdefault(c, []).append((k, a.get(c), b.get(c)))
    by_co = {}
    for k in added:
        by_co[k[0]] = by_co.get(k[0], 0) + 1
    print(f"== {f}: {len(old)} -> {len(new)} | added {len(added)} {by_co} | removed {len(removed)}")
    for c, lst in sorted(changed.items()):
        rows = {x[0] for x in lst}
        print(f"   changed col {c}: {len(lst)} cells in {len(rows)} rows; companies {sorted({x[0][0] for x in lst})}")
    if f == "PL_breakdown.json":
        items = {}
        for k in added:
            items[(k[1], kn[k].get("항목명"))] = items.get((k[1], kn[k].get("항목명")), 0) + 1
        print("   added by item:", sorted(items.items(), key=str))
    if f in ("CSM_waterfall.json", "CSM_amortization.json", "CSM_sensitivity.json"):
        q = {}
        for k in added:
            q[(k[0], k[-1] if f != "CSM_amortization.json" else k[1])] = 0
        print("   added keys sample:", sorted({(k[0], str(k[2] if f=='CSM_waterfall.json' else k[1])) for k in added})[:12])
