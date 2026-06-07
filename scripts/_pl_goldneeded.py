# -*- coding: utf-8 -*-
"""List the PL cells whose Tier-2 breakdown was SUPPRESSED by the reconciliation gate
(scripts/build_pl_breakdown.py): the issued+reinsurance decomposition missed the statement
보험손익 by >25%, so items 2-14 were left blank rather than published wrong.  These are the
genuine hand-built-gold candidates.  Split Q4 annuals (high priority — the PL series is
annual-anchored) from Q1-Q3 (quarterly note vs quarterly statement mismatch; low priority).
Reads data/_derived/pl_breakdown_coverage.json (written by the build)."""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cov = json.loads((ROOT / "data/_derived/pl_breakdown_coverage.json").read_text(encoding="utf-8"))

sup = [r for r in cov if r.get("tier2") == "suppressed"]
by_co = defaultdict(lambda: {"q4": [], "q": []})
for r in sup:
    (by_co[(r["name"], r["code"])]["q4" if r["quarter"].endswith("4Q") else "q"]
     ).append(r["quarter"])

# tally
from collections import Counter  # noqa: E402
tier2 = Counter(r.get("tier2") for r in cov)
print("Tier-2 reconciliation tally:", dict(tier2))
print(f"\nSuppressed-Tier-2 cells: {len(sup)}  "
      f"(Q4 annual: {sum(1 for r in sup if r['quarter'].endswith('4Q'))}, "
      f"Q1-Q3: {sum(1 for r in sup if not r['quarter'].endswith('4Q'))})\n")

print("=== GOLD CANDIDATES — Q4 annual cells with no trustworthy breakdown ===")
ann = sorted([(nm, code, d) for (nm, code), d in by_co.items() if d["q4"]],
             key=lambda x: x[0])
for nm, code, d in ann:
    print(f"  {nm:20} {code}  Q4: {', '.join(sorted(d['q4']))}"
          + (f"   (+Q1-3: {', '.join(sorted(d['q']))})" if d["q"] else ""))

print("\n=== quarterly-only suppressions (low priority; Tier-1 intact) ===")
qonly = sorted([(nm, code, d) for (nm, code), d in by_co.items() if d["q"] and not d["q4"]],
               key=lambda x: x[0])
for nm, code, d in qonly:
    print(f"  {nm:20} {code}  {', '.join(sorted(d['q']))}")
