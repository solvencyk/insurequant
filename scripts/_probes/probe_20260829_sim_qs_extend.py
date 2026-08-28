#!/usr/bin/env python3
"""SIMULATION ONLY — measure what validate_master_tables would report if QS
included 2026.2Q.  Writes nothing; monkeypatches the module-level QS and re-runs
the QS-driven axes using **the gate's own key sets** (coverage_holes /
qoq_scan / spike / wfy / continuity).
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_master_tables as V  # noqa: E402

# exact key sets from V._check_coverage / V._check_qoq_warn
WF_KEYS = ["기초CSM", "신계약CSM", "이자부리", "가정및경험조정", "CSM상각", "기말CSM"]
PL_KEYS = ["보험손익", "생명장기손익", "당기순이익"]
CSM_QOQ = [("신계약CSM", "new_business_csm", True), ("이자부리", "csm_interest_accretion", True),
           ("CSM상각", "csm_amortization", True), ("기말CSM", "csm_closing", False)]

wf = V.load_long(V.WF_PATH)
pl = V.load_long(V.PL_PATH)
cfg = V.load_qoq_cfg()

OLD = list(V.QS)
NEW = OLD + ["2026.2Q"]


def run(qs, label):
    V.QS = qs
    real_wf, known_wf, struct_wf = V.coverage_holes(wf, WF_KEYS)
    real_pl, known_pl, struct_pl = V.coverage_holes(pl, PL_KEYS)
    qrows = V.qoq_scan(wf, CSM_QOQ, 50.0, cfg)
    print(f"\n### {label}  (QS {qs[0]}..{qs[-1]}, n={len(qs)})")
    print(f"    coverage real: CSM={len(real_wf)} PL={len(real_pl)}"
          f" | 2023known={len(known_wf)+len(known_pl)} | struct={len(struct_wf)+len(struct_pl)}")
    print(f"    qoq_warn(CSM only, floor 50억) = {len(qrows)}")
    return {"hole_wf": set(real_wf), "hole_pl": set(real_pl),
            "qoq": {(r[0], r[1], r[2], round(r[3] * 100, 1), r[7]) for r in qrows}}


a = run(OLD, "BEFORE 현행 QS")
b = run(NEW, "AFTER  2026.2Q 포함")

print("\n" + "=" * 78)
print("### DELTA")
print("=" * 78)
for k in ("hole_wf", "hole_pl", "qoq"):
    new, gone = b[k] - a[k], a[k] - b[k]
    print(f"\n{k}: +{len(new)} / -{len(gone)}")
    for r in sorted(new, key=str):
        print("   NEW ", r)
    for r in sorted(gone, key=str):
        print("   GONE", r)

# ---- spike / wfy / continuity ----
print("\n" + "=" * 78)
print("### spike / wfy / continuity")
print("=" * 78)
wf_co: dict = defaultdict(dict)
for (co, q), m in wf.items():
    wf_co[co][q] = m

for qs, tag in ((OLD, "BEFORE"), (NEW, "AFTER")):
    spike, wfy, cont = [], [], []
    for co, qmap in sorted(wf_co.items()):
        for i in range(1, len(qs)):
            p = qmap.get(qs[i - 1], {}).get("기말CSM")
            c = qmap.get(qs[i], {}).get("기말CSM")
            if p is not None and c is not None and abs(p) > 1e-6 and abs((c - p) / p) > 0.50:
                spike.append((co, qs[i - 1], qs[i], round(p, 1), round(c, 1)))
        for fy in ("2023", "2024", "2025", "2026"):
            opens = [(q, qmap[q].get("기초CSM")) for q in qs
                     if q.startswith(fy + ".") and q in qmap and qmap[q].get("기초CSM") is not None]
            if len(opens) < 2:
                continue
            vals = [v for _, v in opens]
            if max(vals) - min(vals) > max(0.005 * abs(max(vals)), 2.0):
                if (co, fy) not in V.WFY_EXCEPTIONS:
                    wfy.append((co, fy, tuple(sorted((q, round(v, 1)) for q, v in opens))))
    fy_q: dict = defaultdict(list)
    for q in qs:
        fy_q[q[:4]].append(q)
    prev_close = {fy: f"{int(fy)-1}.4Q" for fy in fy_q if fy != "2023"}
    for co, qmap in sorted(wf_co.items()):
        for fy, qq in fy_q.items():
            if fy not in prev_close:
                continue
            pc = qmap.get(prev_close[fy], {}).get("기말CSM")
            if pc is None:
                continue
            for q in qq:
                o = qmap.get(q, {}).get("기초CSM")
                if o is None:
                    continue
                if abs(o - pc) > max(0.005 * abs(pc), 2.0):
                    cont.append((co, q, round(o, 1), round(pc, 1), prev_close[fy]))
    print(f"\n{tag}: spike={len(spike)} wfy={len(wfy)} cont={len(cont)}")
    for r in spike:
        print("   SPIKE", r)
    for r in wfy:
        print("   WFY  ", r)
    for r in cont:
        print("   CONT ", r)
