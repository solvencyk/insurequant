"""Read-only: triage the DIFF rows of csm_prior_scan_v2.csv into TRUSTED_RESTATED vs SUSPECT and print them.

TRUSTED_RESTATED = status DIFF and the builder's current-column extraction of the SAME filing reproduces the master (fidelity SAME)
                   and the in-filing consistency flag holds (4Q: prior closing == current opening ; interim: prior opening == annual prior opening)
SMALL_RECLASS    = TRUSTED but only items 3/4 differ (opening, closing identical): interest/assumption reallocation, no stock effect
Writes csm_prior_triage.csv.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE / "csm_prior_scan_v2.csv", encoding="utf-8-sig")))


def tf(x):
    return {"True": True, "False": False}.get(x)


out = []
for r in rows:
    if r["status"] != "DIFF":
        continue
    fid = r["fidelity"]
    cons = tf(r["c_chain_ok"]) if r["later_q"].endswith("4Q") else tf(r["c_open_ok"])
    items = set(r["diff_items"].split(",")) if r["diff_items"] else set()
    if fid == "SAME" and cons is True:
        kind = "SMALL_RECLASS" if items <= {"3", "4"} else "TRUSTED_RESTATED"
    elif fid == "SAME" and cons is None:
        kind = "SMALL_RECLASS_NOCHK" if items <= {"3", "4"} else "UNCHECKED"
    else:
        kind = "SUSPECT"
    out.append({**r, "kind": kind, "cons": cons})
from collections import Counter

print(Counter(o["kind"] for o in out))
for o in out:
    p = [o[f"p{k}"] for k in range(1, 7)]
    m = [o[f"m{k}"] for k in range(1, 7)]
    print(f"{o['kind']:19s} {o['kr']} {o['name'][:7]:7s} later={o['later_q']} prior={o['prior_q']} items={o['diff_items']:9s} fid={o['fidelity']:5s} cons={o['cons']}")
    print(f"      prior {p}")
    print(f"      mast  {m}")
with open(HERE / "csm_prior_triage.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
