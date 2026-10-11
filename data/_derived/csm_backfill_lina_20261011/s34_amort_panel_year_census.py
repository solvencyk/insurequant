# -*- coding: utf-8 -*-
"""Step 34 (read-only census): does data/dart/viz/csm_amort_schedule.json (annual panel) carry the PRIOR-year-end schedule for
other companies too?  For each panel entry: its `buckets.total` (printed 계, or a partial sum when only some year buckets were
read) vs the CSM closing of the same fiscal year and of the year before (CSM_waterfall.json master).
Lina is the confirmed case: the extractor picked the <전기말> table that inherits the <당기말> caption (s33).
Classification (relative difference): exact (<0.05%) to FY(N) / exact to FY(N-1) / neither."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")

panel = json.loads((ROOT / "data/dart/viz/csm_amort_schedule.json").read_text(encoding="utf-8"))["companies"]
wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
close, names = {}, {}
for r in wf:
    if r["항목번호"] == 6 and r.get("값") is not None:
        close[(r["원수사명"], r["공시분기"])] = r["값"]
        names[r["원수사명"]] = r["원보험사코드"]


def find_name(n):
    if n in names:
        return n
    cands = [m for m in names if m.startswith(n) or n.startswith(m) or n in m or m in n]
    return cands[0] if len(cands) == 1 else None


EXACT = 0.0005
out = []
for c in panel:
    nm, per = c.get("company"), c.get("period")
    tot = (c.get("buckets") or {}).get("total")
    y1 = (c.get("yearly") or {}).get("y1")
    mn = find_name(nm)
    rec = {"company": nm, "period": per, "total": tot, "y1": y1, "rcept_no": c.get("rcept_no"), "master_name": mn}
    if not (mn and tot and per and per.startswith("FY")):
        rec["verdict"] = "not comparable (no total or no master closing)"
        out.append(rec)
        continue
    fy = int(per[2:6])
    cN, cP = close.get((mn, f"{fy}.4Q")), close.get((mn, f"{fy - 1}.4Q"))
    dN = None if not cN else abs(tot / cN - 1)
    dP = None if not cP else abs(tot / cP - 1)
    rec.update({"closeN": cN, "closeN-1": cP, "relN": None if dN is None else round(dN, 5), "relN-1": None if dP is None else round(dP, 5)})
    if dP is not None and dP < EXACT and (dN is None or dP < dN):
        rec["verdict"] = "EQUALS FY(N-1) closing -> prior-year-end table likely picked"
    elif dN is not None and dN < EXACT:
        rec["verdict"] = "equals FY(N) closing"
    elif dN is not None and dN < 0.02:
        rec["verdict"] = "within 2% of FY(N) (rounded/partial)"
    else:
        rec["verdict"] = "neither (partial bucket sum or different basis)"
    out.append(rec)
for r in out:
    print(f"  {r['company']:<16s} {r['period']} total={r['total']} closeN={r.get('closeN')} closeN-1={r.get('closeN-1')} relN={r.get('relN')} relN-1={r.get('relN-1')}  {r['verdict']}")
bad = [r for r in out if r["verdict"].startswith("EQUALS FY(N-1)")]
print("\nEQUALS prior-year closing:", len(bad), [r["company"] for r in bad])
(W / "s34_amort_panel_year_census.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
