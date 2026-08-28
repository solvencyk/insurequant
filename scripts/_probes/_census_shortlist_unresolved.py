#!/usr/bin/env python3
"""From the '?' (no same-FY prior quarter to cross-check against) and 'neither-close'
buckets in dart_sign_reversal_census_summary.json, shortlist the ones actually worth a
raw-XML read: keep only rows where (a) master's 값 really was sourced from THIS cache
row (matches cached_add within rounding -- many '?' rows turned out to belong to a
different fs_div/derivation path entirely and are not informative), and (b) |cached_add|
and |cached_amt| are close in magnitude (a real same-period duplicate-with-flipped-sign,
like KR0083/KR0082's exact match, not just two unrelated quarters that happen to have
opposite signs)."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "data" / "_derived" / "dart_sign_reversal_census_summary.json"


def main():
    rows = json.loads(SUMMARY.read_text(encoding="utf-8"))
    shortlisted = []
    for r in rows:
        if r["verdict"] not in ("?", "neither-close(check prev-quarter itself)"):
            continue
        add, amt = r["cached_thstrm_add_amount_mmw"], r["cached_thstrm_amount_mmw"]
        mv = r["master_값"]
        if mv is None or add == 0:
            continue
        if abs(mv - add) > max(1.0, abs(add) * 0.001):
            continue                      # this row isn't actually the cell's source
        if amt == 0:
            continue
        ratio = abs(amt) / abs(add)
        if not (0.5 <= ratio <= 2.0):
            continue                      # not a same-magnitude pair -> ordinary volatility
        shortlisted.append(r)

    print(f"shortlisted from '?'/'neither-close': {len(shortlisted)}")
    for r in shortlisted:
        print(f"  {r['kr_code']} {r['name']} {r['quarter']} item{r['item']} ({r['account_nm']}): "
              f"master={r['master_값']} cached_add={r['cached_thstrm_add_amount_mmw']} "
              f"cached_amt={r['cached_thstrm_amount_mmw']} verdict_was={r['verdict']}")


if __name__ == "__main__":
    main()
