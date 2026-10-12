"""Read-only census: for every DART filing of 2024.1Q..2026.2Q (listed/annual filers on disk) read the PRIOR-period CSM roll-forward
(the comparative column) with the production builder's own pickers and compare it with the CSM_waterfall.json cell block of the
same quarter one year earlier.

Output: csm_prior_scan.csv (one row per later filing)  +  console summary.
status: SAME  (all six items within tolerance)          DIFF (>= 1 item outside tolerance)
        NO_PRIOR (no prior block / builder returned None) NO_MASTER (master has no block for that quarter)  ERR
tolerance per item: max(0.15억, 0.05%) - the master stores 억원 1 decimal.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
import traceback
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import prior_csm as P  # noqa: E402

B = P.B
master = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
M = {}
for r in master:
    M.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
NAMES = {}
for r in master:
    NAMES[r["원보험사코드"]] = r["원수사명"]

LATER = [f"{y}.{n}Q" for y in (2024, 2025, 2026) for n in (1, 2, 3, 4)]
LATER = [q for q in LATER if q <= "2026.2Q"]


def raw_dirs(kr, q):
    fy = f"FY{q[:4]}_Q{q[5]}"
    return sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*"))


def tol(v):
    return max(0.15, abs(v) * 0.0005) if v is not None else 0.15


def main():
    krs = sorted({d.name.split("_")[0] for fy in (ROOT / "data/dart").glob("FY*_Q*") for d in (fy / "raw").glob("KR*") if d.is_dir()})
    out = []
    t0 = time.time()
    annual_prior_open = {}   # (kr, later_year) -> restated opening of the previous year, from the later annual filing's prior column
    for kr in krs:
        name = NAMES.get(kr) or B.META.get(kr, (kr,))[0]
        # pass 1: annual later filings (no anchor)
        for y in (2024, 2025):
            for rd in raw_dirs(kr, f"{y}.4Q"):
                try:
                    pv, src, n = P.prior_waterfall(rd, name, None)
                except Exception:
                    pv = None
                if pv and pv.get(1) is not None:
                    annual_prior_open[(kr, y)] = pv[1]
        for q in LATER:
            for rd in raw_dirs(kr, q):
                y = int(q[:4])
                qprev = f"{y-1}{q[4:]}"
                row = {"kr": kr, "name": name, "later_q": q, "prior_q": qprev, "dir": rd.name}
                try:
                    anchor = None
                    if not q.endswith("4Q"):
                        anchor = annual_prior_open.get((kr, y))
                        if anchor is None:
                            anchor = M.get((kr, f"{y-1}.4Q"), {}).get(1)
                    pv, src, n = P.prior_waterfall(rd, name, anchor)
                    row.update(anchor=anchor, n_prior_blocks=n, src=src)
                    mv = M.get((kr, qprev))
                    if pv is None:
                        row["status"] = "NO_PRIOR"
                    elif not mv:
                        row["status"] = "NO_MASTER"
                    else:
                        diffs = []
                        for k in range(1, 7):
                            a, b = pv.get(k), mv.get(k)
                            if a is None or b is None:
                                diffs.append(None)
                            else:
                                diffs.append(round(a - b, 2))
                        bad = [k for k, d in zip(range(1, 7), diffs) if d is not None and abs(d) > tol(mv.get(k))]
                        row["status"] = "DIFF" if bad else "SAME"
                        row["diff_items"] = ",".join(map(str, bad))
                        row["diffs"] = json.dumps(diffs)
                    for k in range(1, 7):
                        row[f"p{k}"] = (pv or {}).get(k)
                        row[f"m{k}"] = (M.get((kr, qprev)) or {}).get(k)
                except Exception as e:
                    row["status"] = "ERR"
                    row["src"] = f"{type(e).__name__}: {e}"[:200]
                out.append(row)
        print(f"{kr} {name} done {round(time.time()-t0)}s", flush=True)
    cols = ["kr", "name", "later_q", "prior_q", "dir", "status", "diff_items", "diffs", "anchor", "n_prior_blocks", "src"] + \
           [f"p{k}" for k in range(1, 7)] + [f"m{k}" for k in range(1, 7)]
    with open(HERE / "csm_prior_scan.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    from collections import Counter
    print(Counter(r["status"] for r in out))


if __name__ == "__main__":
    main()
