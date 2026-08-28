"""Run build_root_masters.build_pl() ONLY (never main()) to propagate the just-patched
data/dart/viz/pl_breakdown_master.json (KR0070 item6/item7, 2024.4Q/2025.1Q) and the just-fixed
data/_gold/user_pl_cells.json (KR0070 item7 override, 2025.1Q) into root PL_breakdown.json --
then do a FULL before/after combo-diff across every (code,item,quarter) key's 값 AND 값_당분기,
to confirm the changed-cell footprint is EXACTLY what's expected from this ticket:
  - KR0070 item6/item7 값 for 2024.4Q, 2025.1Q (the new YTD figures)
  - KR0070 item6/item7 값_당분기 for 2024.4Q, 2025.1Q (derived from the new YTD)
  - KR0070 item6/item7 값_당분기 for 2025.2Q ONLY (flow-diff ripple: 당분기(2025.2Q) =
    YTD(2025.2Q) - YTD(2025.1Q), and YTD(2025.1Q) just moved -- 2025.2Q's own YTD 값 is
    untouched, and nothing past 2025.2Q should move since only ONE quarter's YTD changed).
No other company, item, or row should be touched (row count identical, no NEW rows, no drops).

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/abl_2024q4_2025q1_build_pl_and_diff.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts import build_root_masters as brm

PL_OUT = brm.PL_OUT

before_rows = json.loads(PL_OUT.read_text(encoding="utf-8"))
before_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): (r.get("값"), r.get("값_당분기"))
              for r in before_rows}

n = brm.build_pl()
print(f"build_pl() wrote {n} rows to {PL_OUT}  (before: {len(before_rows)} rows)")

after_rows = json.loads(PL_OUT.read_text(encoding="utf-8"))
after_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): (r.get("값"), r.get("값_당분기"))
             for r in after_rows}

assert len(before_rows) == len(after_rows), \
    f"ROW COUNT CHANGED {len(before_rows)} -> {len(after_rows)} -- ABORT, do not trust this diff"
assert set(before_idx) == set(after_idx), "row KEY SET changed -- ABORT"

diff_keys = sorted(k for k in before_idx if before_idx[k] != after_idx[k])
print(f"\n{len(diff_keys)} (code,item,quarter) keys changed:")
for code, item, q in diff_keys:
    ob, od = before_idx[(code, item, q)]
    nb, nd = after_idx[(code, item, q)]
    print(f"  {code} item{item:<3d} {q:8s}  값: {ob!r:>14s} -> {nb!r:<14s}  "
          f"값_당분기: {od!r:>14s} -> {nd!r}")

companies = {k[0] for k in diff_keys}
items = {k[1] for k in diff_keys}
quarters = {k[2] for k in diff_keys}
expected_quarters = {"2024.4Q", "2025.1Q", "2025.2Q"}
print(f"\ncompanies touched: {sorted(companies)}")
print(f"items touched: {sorted(items)}")
print(f"quarters touched: {sorted(quarters)}")

ok = (companies == {"KR0070"} and items.issubset({6, 7}) and quarters.issubset(expected_quarters))
print(f"\nSCOPE CHECK: {'OK -- exactly the expected footprint' if ok else '!!! UNEXPECTED SCOPE !!!'}")
if not ok:
    sys.exit(1)
