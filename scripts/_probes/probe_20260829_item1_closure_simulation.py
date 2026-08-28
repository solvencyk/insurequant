"""Full-bucket simulation for the item1 (보험손익) closure equation.

Ticket: inbox/validation/20260829T1500Z__orchestrator__MULTI__insurance_result_closure_missing.md

Claim under test: `1 = 2(생명장기) + 13(자동차) + 14(일반) + 15(기타영업수익) - 16(기타사업비용)`
is NOT checked by scripts/validate_master_tables.py.

This probe measures, over every (company, quarter) bucket of the deployed root master
PL_breakdown.json:
  A. the item-number -> item-name catalog (and any type inconsistency in 항목번호)
  B. presence census of items 1, 2, 13, 14, 15, 16
  C. residual of the bare form (1 = 2+13+14) and adj form (1 = 2+13+14+15-16)
  D. what the EXISTING dual-form block in _check_pl_bridge() actually does per bucket
     (PASS / FAIL / SKIP, and which term caused the SKIP)

Read-only. Writes nothing.
"""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PL_PATH = ROOT / "PL_breakdown.json"

DEFAULT_FLOOR = 200.0  # 백만원, mirrors validate_master_tables.DEFAULT_FLOOR


def norm(s: str) -> str:
    return (s or "").replace(" ", "")


def main() -> None:
    rows = json.loads(PL_PATH.read_text(encoding="utf-8"))

    # ---- A. catalog -----------------------------------------------------
    cat: dict[str, set[str]] = defaultdict(set)
    no_types = Counter()
    for r in rows:
        no = r["항목번호"]
        no_types[type(no).__name__] += 1
        cat[str(no)].add(norm(r["항목명"]))
    print("=" * 78)
    print("A. 항목번호 catalog  (type census: %s)" % dict(no_types))
    print("=" * 78)
    for k in sorted(cat, key=lambda x: (len(x), x)):
        print("  %-4s %s" % (k, " | ".join(sorted(cat[k]))))

    # ---- index by (co, q) ----------------------------------------------
    idx: dict[tuple[str, str], dict[str, float | None]] = defaultdict(dict)
    meta: dict[tuple[str, str], str] = {}
    for r in rows:
        key = (r["원수사명"], r["공시분기"])
        idx[key][norm(r["항목명"])] = r["값"]
        meta[key] = r.get("생손보여부") or "?"

    NM = {
        1: "보험손익", 2: "생명장기손익", 13: "자동차손익", 14: "일반손익",
        15: "기타영업수익", 16: "기타사업비용",
    }
    print()
    print("=" * 78)
    print("B. presence census over %d (회사,분기) buckets" % len(idx))
    print("=" * 78)
    for n, nm in NM.items():
        present = sum(1 for m in idx.values() if m.get(nm) is not None)
        zero = sum(1 for m in idx.values() if m.get(nm) == 0)
        print("  item%-3d %-12s present=%3d  missing=%3d  (of which ==0.0: %d)"
              % (n, nm, present, len(idx) - present, zero))

    # by 생손보
    print("  -- missing split by 생손보여부 --")
    for n, nm in NM.items():
        c = Counter()
        for k, m in idx.items():
            if m.get(nm) is None:
                c[meta[k]] += 1
        print("    item%-3d %-12s missing: %s" % (n, nm, dict(c) or "{}"))

    # ---- C/D. simulation -------------------------------------------------
    stats = Counter()
    bare_only_pass = []      # bare closes, adj does not (or adj unavailable)
    adj_only_pass = []       # adj closes, bare does not
    both_fail = []
    skip_detail = Counter()
    skipped_buckets = []
    residuals_chosen = []
    lifeco_no_lob = []       # bucket where 13/14 missing -> existing block SKIPs

    for (co, q), m in sorted(idx.items()):
        bo = m.get("보험손익")
        lob = [m.get("생명장기손익"), m.get("자동차손익"), m.get("일반손익")]
        oi, oe = m.get("기타영업수익"), m.get("기타사업비용")

        if bo is None or any(x is None for x in lob):
            stats["EXISTING_SKIP"] += 1
            missing = []
            if bo is None:
                missing.append("1보험손익")
            for nm, v in zip(("2생명장기", "13자동차", "14일반"), lob):
                if v is None:
                    missing.append(nm)
            skip_detail[",".join(missing)] += 1
            skipped_buckets.append((co, q, meta[(co, q)], ",".join(missing),
                                    bo, lob[0], lob[1], lob[2], oi, oe))
            if bo is not None and lob[0] is not None:
                lifeco_no_lob.append((co, q, meta[(co, q)]))
            continue

        bare = sum(lob)
        tol = max(0.001 * abs(bo), DEFAULT_FLOOR)
        d_bare = bare - bo
        d_adj = None
        if oi is not None and oe is not None:
            d_adj = bare + oi - oe - bo
        cands = [d_bare] + ([d_adj] if d_adj is not None else [])
        chosen = min(cands, key=abs)
        residuals_chosen.append(abs(chosen))

        ok_bare = abs(d_bare) <= tol
        ok_adj = (d_adj is not None and abs(d_adj) <= tol)
        if ok_bare or ok_adj:
            stats["EXISTING_PASS"] += 1
            if ok_bare and not ok_adj:
                bare_only_pass.append((co, q, bo, d_bare, d_adj))
            elif ok_adj and not ok_bare:
                adj_only_pass.append((co, q, bo, d_bare, d_adj))
            else:
                stats["both_forms_close"] += 1
        else:
            stats["EXISTING_FAIL"] += 1
            both_fail.append((co, q, meta[(co, q)], bo, d_bare, d_adj, tol))

    print()
    print("=" * 78)
    print("C. existing dual-form block verdicts: %s" % dict(stats))
    print("=" * 78)
    print("  -- SKIP reason census (missing terms) --")
    for reason, n in skip_detail.most_common():
        print("    %3d  missing = %s" % (n, reason))

    if residuals_chosen:
        rs = sorted(residuals_chosen)
        print("  -- |chosen residual| distribution over %d checked buckets (백만원) --"
              % len(rs))
        print("     min=%.1f  median=%.1f  p90=%.1f  p99=%.1f  max=%.1f"
              % (rs[0], statistics.median(rs), rs[int(0.9 * (len(rs) - 1))],
                 rs[int(0.99 * (len(rs) - 1))], rs[-1]))

    print("  -- form split --")
    print("     both forms close : %d" % stats["both_forms_close"])
    print("     bare only        : %d" % len(bare_only_pass))
    print("     adj  only        : %d" % len(adj_only_pass))
    for co, q, bo, db, da in adj_only_pass[:20]:
        das = "%.1f" % da if da is not None else "n/a"
        print("        ADJ  %-16s %s  lhs=%.1f  d_bare=%+.1f  d_adj=%s" % (co, q, bo, db, das))

    print("  -- FAIL detail (both forms) --")
    for co, q, kind, bo, db, da, tol in both_fail:
        das = "%.1f" % da if da is not None else "n/a"
        print("     FAIL %-16s %s %-6s lhs=%.1f tol=%.1f d_bare=%+.1f d_adj=%s"
              % (co, q, kind, bo, tol, db, das))

    print()
    print("=" * 78)
    print("D. SKIPPED buckets in full (co, q, 생손보, missing, values)")
    print("=" * 78)
    for co, q, kind, missing, bo, i2, i13, i14, i15, i16 in skipped_buckets:
        def f(v):
            return "None" if v is None else "%.1f" % v
        print("  SKIP %-18s %s %-6s missing=[%s]  1=%s 2=%s 13=%s 14=%s 15=%s 16=%s"
              % (co, q, kind, missing, f(bo), f(i2), f(i13), f(i14), f(i15), f(i16)))

    # companies affected by SKIP
    print()
    skip_co = Counter(co for co, *_ in skipped_buckets)
    print("  SKIP by company (%d companies): %s" % (len(skip_co), dict(skip_co.most_common())))


if __name__ == "__main__":
    main()
