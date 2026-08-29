"""Do the *parallel* identities hold for the hyphenated (extra-LOB) item set?

The gate checks three closure identities on the standard 생명장기 slots:
    item3  = item4  + item5  + item6  + item7      (원수)
    item8  = item9  + item10 + item11 + item12     (재보험)
    item2  = item3  + item8                        (LOB total)

코리안리재보험 publishes a structurally identical parallel set for its 장기재보험
LOB under hyphenated numbers 2-1 … 12-1, but the gate has no equations for them.
This probe measures whether those parallel identities actually close, so the
decision to wire them is made on data rather than symmetry.

Read-only.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLOOR = 200.0     # DEFAULT_FLOOR, 백만원

# (label, lhs 항목번호, [rhs 항목번호...])
STD = [("item3 = 4+5+6+7", "3", ["4", "5", "6", "7"]),
       ("item8 = 9+10+11+12", "8", ["9", "10", "11", "12"]),
       ("item2 = 3+8", "2", ["3", "8"])]
HYP = [("item3-1 = 4-1+5-1+6-1+7-1", "3-1", ["4-1", "5-1", "6-1", "7-1"]),
       ("item8-1 = 9-1+10-1+11-1+12-1", "8-1", ["9-1", "10-1", "11-1", "12-1"]),
       ("item2-1 = 3-1+8-1", "2-1", ["3-1", "8-1"])]


def main() -> None:
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    by: dict = defaultdict(dict)
    for r in rows:
        by[(r["원수사명"], r["공시분기"])][str(r["항목번호"])] = r["값"]

    for title, eqs in (("코리안리재보험 — HYPHEN set (currently unchecked)", HYP),
                       ("코리안리재보험 — STANDARD set (checked by PL_EQS)", STD)):
        print("=" * 78)
        print(title)
        print("=" * 78)
        for label, lhs_no, rhs_nos in eqs:
            print(f"  {label}")
            npass = nfail = nskip = 0
            for (co, q), m in sorted(by.items()):
                if co != "코리안리재보험":
                    continue
                lhs = m.get(lhs_no)
                rhs_vals = [m.get(k) for k in rhs_nos]
                if lhs is None or any(v is None for v in rhs_vals):
                    nskip += 1
                    print(f"      SKIP {q}  lhs={lhs}  rhs={rhs_vals}")
                    continue
                diff = sum(rhs_vals) - lhs
                ok = abs(diff) <= max(0.001 * abs(lhs), FLOOR)
                npass, nfail = (npass + 1, nfail) if ok else (npass, nfail + 1)
                if not ok:
                    print(f"      FAIL {q}  lhs={lhs:,.1f} rhs={sum(rhs_vals):,.1f} diff={diff:+,.1f}")
            print(f"      -> pass={npass} fail={nfail} skip={nskip}")
        print()

    # coverage: how many hyphen cells does ANY rule currently consume?
    print("=" * 78)
    print("hyphen-cell rule coverage (by 항목명, the key load_long() indexes on)")
    print("=" * 78)
    names = {}
    for r in rows:
        no = str(r.get("항목번호"))
        if "-" in no:
            names[no] = r["항목명"]
    # exact-token references found by grep across scripts/validate_*.py
    CONSUMED = {"4-1"}      # 수재CSM상각 -> CSM_AMORT_PL_LEGS
    for no in sorted(names, key=lambda s: (int(s.split("-")[0]), s)):
        n_cells = sum(1 for r in rows if str(r.get("항목번호")) == no)
        tag = "CONSUMED by CSM_AMORT_PL_LEGS" if no in CONSUMED else "NO RULE READS THIS"
        print(f"  {no:>5s}  {names[no]:<24s} cells={n_cells:>3d}  {tag}")


if __name__ == "__main__":
    main()
