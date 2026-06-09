# -*- coding: utf-8 -*-
"""TIER-1 coverage audit.  For every (company, quarter) discovered in data/dart, ask the
FS-API tier1_for() and report:
  • HTML  — FS-API returned None (build falls back to the fragile HTML income-statement parser)
  • items present among the Tier-1 set {1 보험손익, 17 투자손익, 20 영업이익, 22 세전, 24 당기순}
A company-quarter that is FS-API-sourced but MISSING a Tier-1 item is the actionable gap.
Read-only; uses the on-disk FS cache so it does not hammer DART.
"""
from __future__ import annotations
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_pl_breakdown import discover_filings, load_universe
from scripts.fetch_dart_fs import tier1_for

TIER1 = {1: "보험손익", 17: "투자손익", 20: "영업이익", 22: "세전", 24: "당기순"}
QORDER = [f"{y}.{q}Q" for y in range(2023, 2027) for q in range(1, 5) if not (y == 2026 and q > 1)]


def main() -> int:
    uni = load_universe()
    filings = discover_filings()
    html, miss = [], []
    n_api = 0
    for code in sorted(filings):
        name, life = uni.get(code, (None, None))
        if name is None:
            continue
        for q in QORDER:
            if q not in filings[code]:
                continue
            try:
                t1 = tier1_for(name, q, code)
            except Exception as e:
                t1 = None
            if not t1:
                html.append((code, name, q))
                continue
            n_api += 1
            absent = [i for i in TIER1 if t1.get(i) is None]
            if absent:
                miss.append((code, name, q, absent))

    print("=" * 76)
    print(f"TIER-1 AUDIT  FS-API ok={n_api}  HTML-fallback={len(html)}  with-missing-item={len(miss)}")
    print("=" * 76)
    print("\n-- HTML fallback (FS-API returned nothing) --")
    by_q = defaultdict(list)
    for code, name, q in html:
        by_q[q].append(name)
    for q in QORDER:
        if by_q[q]:
            print(f"  {q}: {', '.join(sorted(by_q[q]))}")
    print("\n-- FS-API present but MISSING a Tier-1 item --")
    for code, name, q, absent in sorted(miss, key=lambda t: (t[1], t[2])):
        print(f"  {name:16s} {q}  missing={[TIER1[i] for i in absent]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
