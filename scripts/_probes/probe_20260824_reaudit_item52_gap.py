# -*- coding: utf-8 -*-
"""Read-only: what does the gate do when item52 (TFI 지급여력금액) is missing?

KR0004 raw prints the row; the master does not carry it in 4 quarters.
Prints every 50_tfi_tier_split finding for KR0003/KR0004 with full status+detail.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

CODES = ("KR0003", "KR0004")


def main() -> None:
    from src.solvency.validation.kics_json_rules import run_validation
    from validate_kics_disclosure import _load_tfi_applicability

    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    res = run_validation(rows, tfi_applicability=_load_tfi_applicability())
    findings = res["findings"] if isinstance(res, dict) else res

    print("=== 50_tfi_tier_split{,_post} for KR0003 / KR0004 ===")
    for x in findings:
        if x["원보험사코드"] not in CODES:
            continue
        if not x["rule"].startswith("50_tfi_tier_split"):
            continue
        print(f"  {x['원보험사코드']} {x['공시분기']:<9} {x['rule']:<24} "
              f"{x['status']:<7} diff={x.get('diff')}")
        print(f"        {x.get('detail','')[:230]}")

    # repo-wide: how many buckets are missing item52 while having 50/51?
    print("\n=== repo-wide census: item50/51 present but item52 missing (값) ===")
    grid: dict[tuple[str, str], dict[int, dict]] = {}
    for r in rows:
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        grid.setdefault((r.get("원보험사코드"), r.get("공시분기")), {})[it] = r
    n = 0
    for k in sorted(grid):
        d = grid[k]
        has50 = 50 in d and str(d[50].get("값") or "") != ""
        has51 = 51 in d and str(d[51].get("값") or "") != ""
        has52 = 52 in d and str(d[52].get("값") or "") != ""
        if has50 and has51 and not has52:
            n += 1
            print(f"   {k[0]} {k[1]}")
    print(f"   total = {n}")


if __name__ == "__main__":
    main()
