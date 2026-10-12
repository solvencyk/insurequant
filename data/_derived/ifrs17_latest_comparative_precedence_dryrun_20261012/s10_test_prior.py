"""Read-only self-test of prior_csm: for (KR, later-filing quarter) print master(year-1 same quarter) vs prior-column extraction.

usage: python s10_test_prior.py KR0011:2024.1Q KR0073:2024.2Q ...
"""
from __future__ import annotations

import json
import sys
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


def raw_dirs(kr, q):
    fy = f"FY{q[:4]}_Q{q[5]}"
    return sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*"))


for spec in sys.argv[1:]:
    kr, q = spec.split(":")
    y = int(q[:4])
    qprev = f"{y-1}{q[4:]}"
    name = B.META.get(kr, (kr,))[0]
    for rd in raw_dirs(kr, q):
        # anchor = year-(y-1) opening as seen in the later annual filing's prior column, else master's same-year opening
        anchor = None
        a_rds = raw_dirs(kr, f"{y}.4Q")
        if a_rds and not q.endswith("4Q"):
            pv, _s, _n = P.prior_waterfall(a_rds[0], name, None)
            if pv:
                anchor = pv.get(1)
        pv, src, n = P.prior_waterfall(rd, name, None if q.endswith("4Q") else anchor)
        cur, csrc = P.current_waterfall(rd, name, None)
        print(f"== {kr} {name} later={q} prior_blocks={n} anchor={anchor}")
        print("   master[%s]   " % qprev, {k: M.get((kr, qprev), {}).get(k) for k in range(1, 7)})
        print("   prior-col     ", pv, src)
        print("   master[%s]   " % q, {k: M.get((kr, q), {}).get(k) for k in range(1, 7)})
        print("   current-col   ", cur, csrc)
