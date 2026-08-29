"""Tautology check on the hyphenated (extra-LOB) parent-child identities.

The 3 parallel identities (2-1 = 3-1+8-1, 3-1 = 4-1..7-1, 8-1 = 9-1..12-1) close
14/14 — but "closes" is not "verifies".  `scripts/pl_breakdown/companies.py::leg()`
builds the parallel set as
    {2: suje + chuljae, 3: suje, 7: suje - csm - ra - yes,
     8: chuljae, 12: chuljae - recsm - rera - reyes, ...}
i.e. items 7 and 12 are PLUGS and item 2 is a SUM.  If so the three identities are
true by construction and wiring them would manufacture coverage, not verification
(tests/test_identity_tautology.py's exact failure mode; CLAUDE.md "등식은 0들로도
닫힌다").

Residual distribution decides it: an exactly-0 residual on every bucket means the
value was reconciled into the identity before storage, not read from the source.

Read-only.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EQS = [("2-1 = 3-1 + 8-1", "2-1", ["3-1", "8-1"]),
       ("3-1 = 4-1+5-1+6-1+7-1", "3-1", ["4-1", "5-1", "6-1", "7-1"]),
       ("8-1 = 9-1+10-1+11-1+12-1", "8-1", ["9-1", "10-1", "11-1", "12-1"]),
       # same shape on the STANDARD slots, for comparison
       ("2 = 3 + 8", "2", ["3", "8"]),
       ("3 = 4+5+6+7", "3", ["4", "5", "6", "7"]),
       ("8 = 9+10+11+12", "8", ["9", "10", "11", "12"])]


def main() -> None:
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    by: dict = defaultdict(dict)
    for r in rows:
        by[(r["원수사명"], r["공시분기"])][str(r["항목번호"])] = r["값"]

    print("Residual distribution — 코리안리재보험 only (the sole carrier of hyphen items)")
    print(f"{'equation':<26s}{'n':>4s}{'exact0':>8s}{'<1e-6':>8s}{'max|res|':>14s}")
    print("-" * 60)
    for label, lhs_no, rhs_nos in EQS:
        res = []
        for (co, q), m in sorted(by.items()):
            if co != "코리안리재보험":
                continue
            lhs = m.get(lhs_no)
            vals = [m.get(k) for k in rhs_nos]
            if lhs is None or any(v is None for v in vals):
                continue
            res.append(abs(sum(vals) - lhs))
        n0 = sum(1 for r in res if r == 0.0)
        n6 = sum(1 for r in res if r < 1e-6)
        print(f"{label:<26s}{len(res):>4d}{n0:>8d}{n6:>8d}{(max(res) if res else 0):>14.9f}")

    print()
    print("For contrast — the SAME 3-slot shape across ALL companies (standard slots),")
    print("which is what the existing PL_EQS actually run on:")
    for label, lhs_no, rhs_nos in EQS[3:]:
        res = []
        for (co, q), m in sorted(by.items()):
            lhs = m.get(lhs_no)
            vals = [m.get(k) for k in rhs_nos]
            if lhs is None or any(v is None for v in vals):
                continue
            res.append(abs(sum(vals) - lhs))
        n0 = sum(1 for r in res if r == 0.0)
        print(f"  {label:<24s} n={len(res):>4d}  exact0={n0:>4d} ({n0/max(len(res),1)*100:5.1f}%)"
              f"  max|res|={max(res) if res else 0:,.6f}")


if __name__ == "__main__":
    main()
