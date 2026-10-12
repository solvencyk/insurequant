"""Read-only: refine the PL Tier-1 census - separate pure SIGN FLIPS (XBRL sign-convention noise) from real value changes.

Reads pl_tier1_scan.csv, writes pl_tier1_scan_refined.csv with column kind in
  SIGN_FLIP   |later| == |master| (tol 0.01%) with opposite sign
  REAL_SMALL  relative change <= 1%
  REAL_LARGE  relative change > 1%
and prints block-level counts: a (company, quarter) block is REAL if it has >=1 REAL_* cell.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE / "pl_tier1_scan.csv", encoding="utf-8-sig")))


def f(x):
    try:
        return float(x)
    except Exception:
        return None


out = []
for r in rows:
    if r["cls"] != "RESTATED_STALE":
        continue
    m, l = f(r["master"]), f(r["later"])
    if m is None or l is None:
        kind = "ONE_SIDE_MISSING"
    elif abs(abs(m) - abs(l)) <= max(1.0, 1e-4 * max(abs(m), abs(l))) and m * l < 0:
        kind = "SIGN_FLIP"
    else:
        rel = abs(m - l) / max(abs(m), abs(l), 1e-9)
        kind = "REAL_SMALL" if rel <= 0.01 else "REAL_LARGE"
    out.append({**r, "kind": kind})

with open(HERE / "pl_tier1_scan_refined.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

print("RESTATED_STALE by kind:", dict(Counter(r["kind"] for r in out)))
blocks = defaultdict(Counter)
for r in out:
    blocks[(r["kr"], r["quarter"])][r["kind"]] += 1
real_blocks = [k for k, c in blocks.items() if c["REAL_SMALL"] or c["REAL_LARGE"]]
flip_only = [k for k, c in blocks.items() if not (c["REAL_SMALL"] or c["REAL_LARGE"]) and c["SIGN_FLIP"]]
print("blocks with real change:", len(real_blocks), " sign-flip only:", len(flip_only))
by_co = Counter(k[0] for k in real_blocks)
print("real blocks by company:", dict(sorted(by_co.items())))
by_it = Counter(r["item"] for r in out if r["kind"] in ("REAL_SMALL", "REAL_LARGE"))
print("real cells by item:", dict(sorted(by_it.items(), key=lambda kv: int(kv[0]))))
print("---- REAL cells of the main aggregates (item 1, 20, 22, 24) ")
for r in out:
    if r["kind"] in ("REAL_SMALL", "REAL_LARGE") and r["item"] in ("1", "20", "22", "24"):
        print(r["kr"], r["name"][:6], r["quarter"], "item", r["item"], "master", r["master"][:14], "later", r["later"][:14], r["kind"], r["basis_orig"], r["basis_later"])
