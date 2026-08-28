"""Second-stage simulation: what do the 71 silent SKIPs of the 보험손익(dual) bridge hide?

Ticket: inbox/validation/20260829T1500Z__orchestrator__MULTI__insurance_result_closure_missing.md

The existing dual-form block in validate_master_tables._check_pl_bridge() skips a bucket
whenever item1/2/13/14 is None. This probe asks the only question that separates
"legitimately absent leg" from "extraction gap":

    if we treat every MISSING LOB leg as 0.0, does the identity close?

  - closes  -> the absent leg really is zero for that issuer (the LOB is not written),
              so the SKIP was hiding nothing; the bucket can be checked with 0-fill.
  - breaks  -> the missing leg carries real money that nothing in the gate is looking at.
              Residual = lower bound on the size of the unchecked hole.

Also measures whether the PL coverage census (key_items = 보험손익/생명장기손익/당기순이익)
would have caught these, and whether QS covers every quarter present in the master.

Read-only. Writes nothing.
"""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PL_PATH = ROOT / "PL_breakdown.json"
DEFAULT_FLOOR = 200.0

QS_IN_GATE = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q",
              "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"]
COVERAGE_KEY_ITEMS = ["보험손익", "생명장기손익", "당기순이익"]


def norm(s: str) -> str:
    return (s or "").replace(" ", "")


def main() -> None:
    rows = json.loads(PL_PATH.read_text(encoding="utf-8"))
    idx: dict[tuple[str, str], dict[str, float | None]] = defaultdict(dict)
    meta: dict[tuple[str, str], str] = {}
    for r in rows:
        key = (r["원수사명"], r["공시분기"])
        idx[key][norm(r["항목명"])] = r["값"]
        meta[key] = r.get("생손보여부") or "?"

    # ---- 0. quarter coverage of the gate's QS list -----------------------
    qs_data = sorted({q for _, q in idx})
    outside = [q for q in qs_data if q not in QS_IN_GATE]
    print("=" * 78)
    print("0. quarters present in master vs gate QS list")
    print("=" * 78)
    print("  master quarters : %s" % ", ".join(qs_data))
    print("  NOT in gate QS  : %s" % (", ".join(outside) or "(none)"))
    n_out = sum(1 for k in idx if k[1] in outside)
    print("  buckets in quarters the gate's QS list does not enumerate: %d" % n_out)

    # ---- 1. zero-fill simulation over the SKIP population -----------------
    verdict = Counter()
    closes_zf, breaks_zf, uneval = [], [], []

    for (co, q), m in sorted(idx.items()):
        bo = m.get("보험손익")
        i2, i13, i14 = m.get("생명장기손익"), m.get("자동차손익"), m.get("일반손익")
        oi, oe = m.get("기타영업수익"), m.get("기타사업비용")

        checked_today = (bo is not None and i2 is not None
                         and i13 is not None and i14 is not None)
        if checked_today:
            verdict["CHECKED_TODAY"] += 1
            continue

        if bo is None:
            # LHS itself absent -> the identity cannot be evaluated in any form.
            verdict["UNEVALUABLE_no_item1"] += 1
            present_legs = [n for n, v in (("2", i2), ("13", i13), ("14", i14))
                            if v is not None]
            uneval.append((co, q, meta[(co, q)], "item1=None",
                           "legs present: " + (",".join(present_legs) or "none")))
            continue

        # zero-fill the missing LOB legs
        zf = [0.0 if v is None else v for v in (i2, i13, i14)]
        missing = [n for n, v in (("2생명장기", i2), ("13자동차", i13), ("14일반", i14))
                   if v is None]
        bare = sum(zf)
        tol = max(0.001 * abs(bo), DEFAULT_FLOOR)
        cands = [bare - bo]
        if oi is not None and oe is not None:
            cands.append(bare + oi - oe - bo)
        # also allow 0-filled adj (기타 legs themselves missing)
        oi0 = 0.0 if oi is None else oi
        oe0 = 0.0 if oe is None else oe
        cands.append(bare + oi0 - oe0 - bo)
        chosen = min(cands, key=abs)

        if abs(chosen) <= tol:
            verdict["SKIP_CLOSES_WITH_ZEROFILL"] += 1
            closes_zf.append((co, q, meta[(co, q)], ",".join(missing), bo, chosen, tol))
        else:
            verdict["SKIP_BREAKS_WITH_ZEROFILL"] += 1
            breaks_zf.append((co, q, meta[(co, q)], ",".join(missing), bo, chosen, tol))

    print()
    print("=" * 78)
    print("1. zero-fill verdict over %d buckets: %s" % (len(idx), dict(verdict)))
    print("=" * 78)

    print("  -- (a) SKIP that CLOSES with 0-fill (absent leg really is zero) : %d --"
          % len(closes_zf))
    for co, q, kind, missing, bo, resid, tol in closes_zf:
        print("     ZF-OK   %-18s %s %-6s missing=[%s] lhs=%10.1f resid=%+9.1f tol=%.1f"
              % (co, q, kind, missing, bo, resid, tol))

    print()
    print("  -- (b) SKIP that BREAKS with 0-fill (missing leg carries real money) : %d --"
          % len(breaks_zf))
    for co, q, kind, missing, bo, resid, tol in breaks_zf:
        print("     ZF-RED  %-18s %s %-6s missing=[%s] lhs=%10.1f resid=%+9.1f tol=%.1f"
              % (co, q, kind, missing, bo, resid, tol))
    if breaks_zf:
        mags = sorted(abs(r[5]) for r in breaks_zf)
        print("     residual magnitude (백만원): min=%.1f median=%.1f p90=%.1f max=%.1f"
              % (mags[0], statistics.median(mags), mags[int(0.9 * (len(mags) - 1))], mags[-1]))
        print("     total unchecked |residual| = %.1f 백만원 = %.0f 억원"
              % (sum(mags), sum(mags) / 100.0))
        byco = Counter(r[0] for r in breaks_zf)
        print("     by company: %s" % dict(byco.most_common()))

    print()
    print("  -- (c) UNEVALUABLE (item1 itself missing) : %d --" % len(uneval))
    for co, q, kind, why, legs in uneval:
        print("     NO-LHS  %-18s %s %-6s %s (%s)" % (co, q, kind, why, legs))

    # ---- 2. would the PL coverage census have caught the (b) rows? --------
    print()
    print("=" * 78)
    print("2. does the existing PL coverage census see these? "
          "(key_items = %s)" % COVERAGE_KEY_ITEMS)
    print("=" * 78)
    seen = notseen = 0
    for co, q, kind, missing, bo, resid, tol in breaks_zf:
        m = idx[(co, q)]
        vals = [m.get(k) for k in COVERAGE_KEY_ITEMS]
        in_qs = q in QS_IN_GATE
        flagged = in_qs and not q.startswith("2023.") and any(v is None for v in vals)
        if flagged:
            seen += 1
        else:
            notseen += 1
            reasons = []
            if not in_qs:
                reasons.append("quarter outside QS")
            elif q.startswith("2023."):
                reasons.append("2023 = known(비노출), not a real hole")
            if all(v is not None for v in vals):
                reasons.append("all 3 key_items present (13/14/15/16 not key_items)")
            print("     UNSEEN  %-18s %s  missing=[%s] resid=%+.1f  <- %s"
                  % (co, q, missing, resid, "; ".join(reasons)))
    print("     coverage census would flag: %d / would MISS: %d" % (seen, notseen))


if __name__ == "__main__":
    main()
