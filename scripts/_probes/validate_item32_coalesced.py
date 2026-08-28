"""Same as validate_item32_full_universe.py but treats a missing (None) 26/27/28/29/30 term
as 0 rather than skipping the cell -- this matches the ORIGINAL census's counting convention
(scripts/_probes/oci_full_universe_census.py sums whatever leaf rows actually exist in the
window; a company with no FVOCI-equity row simply contributes nothing to that sum, which is
equivalent to treating a structurally-absent item as 0).  Gives a number directly comparable
to the ticket's stated "282 cells, 270 (96%) reconcile" benchmark.

item32 itself is NOT coalesced -- if item32 is None (the window couldn't even be bounded, e.g.
삼성화재's 9 source-gap quarters), the cell is excluded, since there's no meaningful
"öther OCI" content to attribute at all (not just one named slot silent)."""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import resolve_corp, tier1_for  # noqa: E402

d = json.load(open("PL_breakdown.json", encoding="utf-8"))
by_cq = defaultdict(dict)
name_by_code = {}
for r in d:
    key = (r["원보험사코드"], r["공시분기"])
    by_cq[key][r["항목번호"]] = r["값"]
    name_by_code[r["원보험사코드"]] = r["원수사명"]

targets = [(code, q) for (code, q), items in by_cq.items() if 25 in items and items[25] is not None]

reconciled, close, unresolved, no_item32 = [], [], [], []
for code, q in sorted(targets):
    name = name_by_code[code]
    cc = resolve_corp(name)
    t1 = tier1_for(name, q, code) if cc else None
    v32 = (t1 or {}).get(32)
    if v32 is None:
        no_item32.append((code, name, q))
        continue
    items = by_cq[(code, q)]
    it25 = items.get(25)
    total = sum((items.get(k) or 0) for k in (26, 27, 28, 29, 30)) + v32
    resid = it25 - total
    rel = abs(resid) / max(abs(it25), abs(total), 1e-9)
    row = (code, name, q, it25, total, resid, rel)
    if rel <= 0.01:
        reconciled.append(row)
    elif rel <= 0.05:
        close.append(row)
    else:
        unresolved.append(row)

total_n = len(targets)
print(f"total 282-equivalent cells (item25 present, non-null): {total_n}")
print(f"item32 itself absent (source has no OCI leaf detail at all -- e.g. 삼성화재): {len(no_item32)}")
by_code = defaultdict(int)
for code, name, q in no_item32:
    by_code[(code, name)] += 1
for (code, name), n in sorted(by_code.items(), key=lambda x: -x[1]):
    print(f"   {code} {name}: {n}")

evaluated = len(reconciled) + len(close) + len(unresolved)
print(f"\nevaluated (item32 computable): {evaluated}")
print(f"  reconciled (<=1%): {len(reconciled)}  ({len(reconciled)/total_n*100:.1f}% of all {total_n})")
print(f"  close (1-5%):      {len(close)}")
print(f"  unresolved (>5%):  {len(unresolved)}")
print(f"\nGRAND TOTAL reconciled-or-explained: {len(reconciled)} reconciled + {len(no_item32)} "
      f"documented source-gap = {len(reconciled) + len(no_item32)}/{total_n} "
      f"({(len(reconciled) + len(no_item32))/total_n*100:.1f}%)")

print("\n=== close (1-5%) ===")
for code, name, q, it25, total, resid, rel in close:
    print(f"  {name}({code}) {q}: item25={it25:,.3f} sum={total:,.3f} resid={resid:,.3f} rel={rel:.2%}")
print("\n=== unresolved (>5%) ===")
for code, name, q, it25, total, resid, rel in unresolved:
    print(f"  {name}({code}) {q}: item25={it25:,.3f} sum={total:,.3f} resid={resid:,.3f} rel={rel:.2%}")
