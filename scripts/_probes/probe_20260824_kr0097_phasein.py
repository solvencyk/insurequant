"""Read-only: test the phase-in derivation  after = max(0, before - (1-r)*initial)
for KR0097 (하나생명) 생명장기 sub-risks, and check R7 aggregation against the
published item17_after for every quarter.

initial amounts (2023-03-31 basis, 천원 -> 억원) come from the FY2024_Q4 filing p326:
  장수 14,325,093 / 해지 66,403,015 / 사업비 43,877,926 / 대재해 7,847,532
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import validate_kics_disclosure as V  # noqa: E402
from solvency.validation.kics_json_rules import R7  # noqa: E402

INITIAL = {30: 143.25093, 33: 664.03015, 34: 438.77926, 35: 78.47532}
# recognition ratio by year (p326: 2024 = 10%); phase-in schedule 10%/yr from 2023.
RATIO = {"2023": 0.0, "2024": 0.10, "2025": 0.20, "2026": 0.30}


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def main():
    recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    rows = {}
    for r in recs:
        if r.get("원보험사코드") != "KR0097":
            continue
        rows.setdefault(r["공시분기"], {})[int(r["항목번호"])] = (_num(r.get("값")),
                                                                _num(r.get("값_적용후")))
    for q in sorted(rows):
        m = rows[q]
        yr = q.split(".")[0]
        r = RATIO.get(yr)
        pre = [m.get(i, (None, None))[0] for i in range(29, 36)]
        post_master = [m.get(i, (None, None))[1] for i in range(29, 36)]
        if any(p is None for p in pre):
            print(f"{q}: pre incomplete {pre}")
            continue
        derived = []
        for k, i in enumerate(range(29, 36)):
            init = INITIAL.get(i)
            if init is None:
                derived.append(pre[k])
            else:
                derived.append(max(0.0, pre[k] - (1 - r) * init))
        agg_der = V._diversified_sqrt(np.array(derived, dtype=float), R7)
        p17_post = m.get(17, (None, None))[1]
        p17_pre = m.get(17, (None, None))[0]
        agg_pre = V._diversified_sqrt(np.array(pre, dtype=float), R7)
        ok_master = all(x is not None for x in post_master)
        agg_master = (V._diversified_sqrt(np.array(post_master, dtype=float), R7)
                      if ok_master else None)
        print(f"{q}  ratio={r}")
        print(f"    pre       = {[round(x, 2) for x in pre]}  R7={agg_pre:.2f} vs item17전={p17_pre}")
        print(f"    master후  = {post_master}"
              + (f"  R7={agg_master:.2f}" if agg_master is not None else "  R7=n/a")
              + f"  vs item17후={p17_post}")
        print(f"    derived후 = {[round(x, 2) for x in derived]}  R7={agg_der:.2f}"
              + (f"  diff vs item17후 = {agg_der - p17_post:+.2f}"
                 if p17_post is not None else ""))


if __name__ == "__main__":
    main()
