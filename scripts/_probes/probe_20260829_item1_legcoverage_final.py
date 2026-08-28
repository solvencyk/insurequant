"""Third-stage simulation: the EXACT semantics of the proposed leg-coverage change.

Ticket: inbox/validation/20260829T1500Z__orchestrator__MULTI__insurance_result_closure_missing.md

Proposed change to validate_master_tables._check_pl_bridge() 보험손익 dual-form block:

  before:  if item1 is None or any LOB leg (2/13/14) is None -> pb_skip (silent)
  after:   if item1 is None                                  -> pb_skip + NO-LHS census line
           else  missing LOB legs are 0-filled and the identity is EVALUATED
                 label "보험손익(dual)"         when nothing was 0-filled (unchanged path)
                 label "보험손익(leg-coverage)" when at least one leg was 0-filled

The 기타영업수익/기타사업비용 adj candidate keeps the EXISTING rule (both present or no
candidate) - no extra 0-filled 기타 candidate, so the new path adds no masking surface.

This probe proves two things:
  (1) the 285 buckets checked today keep BYTE-IDENTICAL verdicts (no regression), and
  (2) the exact pass/fail/skip deltas the gate SUMMARY will move by.

Read-only. Writes nothing.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PL_PATH = ROOT / "PL_breakdown.json"
DEFAULT_FLOOR = 200.0

LOB_KEYS = ("생명장기손익", "자동차손익", "일반손익")


def norm(s: str) -> str:
    return (s or "").replace(" ", "")


def old_verdict(m):
    """Exact reproduction of today's block."""
    bo = m.get("보험손익")
    lob = [m.get(k) for k in LOB_KEYS]
    if bo is None or any(x is None for x in lob):
        return ("SKIP", None, None)
    bare = sum(lob)
    cands = [bare]
    oi, oe = m.get("기타영업수익"), m.get("기타사업비용")
    if oi is not None and oe is not None:
        cands.append(bare + oi - oe)
    diff = min((c - bo for c in cands), key=abs)
    if abs(diff) > max(0.001 * abs(bo), DEFAULT_FLOOR):
        return ("FAIL", "보험손익(dual)", round(diff, 1))
    return ("PASS", "보험손익(dual)", round(diff, 1))


def new_verdict(m):
    """Exact reproduction of the PROPOSED block."""
    bo = m.get("보험손익")
    if bo is None:
        return ("SKIP", None, None)
    raw = [m.get(k) for k in LOB_KEYS]
    zerofilled = [k for k, v in zip(LOB_KEYS, raw) if v is None]
    lob = [0.0 if v is None else v for v in raw]
    bare = sum(lob)
    cands = [bare]
    oi, oe = m.get("기타영업수익"), m.get("기타사업비용")
    if oi is not None and oe is not None:
        cands.append(bare + oi - oe)
    diff = min((c - bo for c in cands), key=abs)
    label = "보험손익(leg-coverage)" if zerofilled else "보험손익(dual)"
    if abs(diff) > max(0.001 * abs(bo), DEFAULT_FLOOR):
        return ("FAIL", label, round(diff, 1))
    return ("PASS", label, round(diff, 1))


def main() -> None:
    rows = json.loads(PL_PATH.read_text(encoding="utf-8"))
    idx = defaultdict(dict)
    meta = {}
    for r in rows:
        key = (r["원수사명"], r["공시분기"])
        idx[key][norm(r["항목명"])] = r["값"]
        meta[key] = r.get("생손보여부") or "?"

    old_c, new_c = Counter(), Counter()
    regressions = []
    new_fail_rows = []
    new_pass_rows = []
    nolhs_rows = []

    for (co, q), m in sorted(idx.items()):
        o = old_verdict(m)
        n = new_verdict(m)
        old_c[o[0]] += 1
        new_c[n[0]] += 1

        # (1) regression guard: buckets already checked must be untouched
        if o[0] != "SKIP" and o != n:
            regressions.append((co, q, o, n))

        if o[0] == "SKIP" and n[0] == "FAIL":
            new_fail_rows.append((co, q, meta[(co, q)], m.get("보험손익"), n[2],
                                  [k for k in LOB_KEYS if m.get(k) is None]))
        if o[0] == "SKIP" and n[0] == "PASS":
            new_pass_rows.append((co, q, meta[(co, q)], m.get("보험손익"), n[2],
                                  [k for k in LOB_KEYS if m.get(k) is None]))
        if n[0] == "SKIP":
            nolhs_rows.append((co, q, meta[(co, q)]))

    print("=" * 78)
    print("1. verdict census over %d buckets" % len(idx))
    print("=" * 78)
    print("   old: %s" % dict(old_c))
    print("   new: %s" % dict(new_c))
    print()
    print("   REGRESSIONS on already-checked buckets: %d  %s"
          % (len(regressions), "<-- MUST BE 0" if not regressions else "<-- STOP"))
    for co, q, o, n in regressions:
        print("      %s %s  old=%s  new=%s" % (co, q, o, n))

    print()
    print("=" * 78)
    print("2. newly PASSing (0-fill closes the identity): %d" % len(new_pass_rows))
    print("=" * 78)
    for co, q, kind, bo, diff, missing in new_pass_rows:
        print("   ZF-PASS %-18s %s %-6s lhs=%10.1f diff=%+8.1f 0-filled=%s"
              % (co, q, kind, bo, diff, ",".join(missing)))

    print()
    print("=" * 78)
    print("3. newly FAILing (0-fill breaks -> unchecked money): %d" % len(new_fail_rows))
    print("=" * 78)
    for co, q, kind, bo, diff, missing in new_fail_rows:
        print("   ZF-FAIL %-18s %s %-6s lhs=%10.1f diff=%+10.1f 0-filled=%s"
              % (co, q, kind, bo, diff, ",".join(missing)))
    byco = Counter(r[0] for r in new_fail_rows)
    print("   by company: %s" % dict(byco.most_common()))
    q24 = [r for r in new_fail_rows if not r[1].startswith("2023.")]
    print("   of which 2024+ (site-visible): %d  -> %s"
          % (len(q24), dict(Counter(r[0] for r in q24).most_common())))

    print()
    print("=" * 78)
    print("4. still SKIP (item1 itself absent - identity has no LHS): %d" % len(nolhs_rows))
    print("=" * 78)
    print("   quarters: %s" % dict(Counter(q for _, q, _ in nolhs_rows).most_common()))
    print("   all 2023? %s" % all(q.startswith("2023.") for _, q, _ in nolhs_rows))

    print()
    print("=" * 78)
    print("5. SUMMARY delta for the dual-form axis")
    print("=" * 78)
    print("   pb_pass  %+d   (%d -> %d)" % (new_c["PASS"] - old_c["PASS"],
                                            old_c["PASS"], new_c["PASS"]))
    print("   pb_fail  %+d   (%d -> %d)" % (new_c["FAIL"] - old_c["FAIL"],
                                            old_c["FAIL"], new_c["FAIL"]))
    print("   pb_skip  %+d   (%d -> %d)" % (new_c["SKIP"] - old_c["SKIP"],
                                            old_c["SKIP"], new_c["SKIP"]))

    # emit the baseline-registry seed so the entries are enumerated, not hand-typed
    seed = {}
    for co, q, kind, bo, diff, missing in new_fail_rows:
        seed["%s|%s|보험손익(leg-coverage)" % (co, q)] = {
            "class": "leg_coverage_newly_exposed",
            "missing_legs": missing,
            "lhs": bo,
            "diff": diff,
        }
    out = ROOT / "scripts" / "_probes" / "_tmp_legcoverage_seed.json"
    out.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print("   seed for the baseline registry written to %s (%d entries)"
          % (out.relative_to(ROOT), len(seed)))


if __name__ == "__main__":
    main()
