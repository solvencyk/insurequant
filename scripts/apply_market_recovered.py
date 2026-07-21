# -*- coding: utf-8 -*-
"""Phase 3 of the 시장위험 36-46 recovery: apply the Workflow's reconcile-gated
results into kics_disclosure.json (single writer).

Input: artifacts/kics_validation/wf_results.json — the recover-market-subrisks
Workflow's return value (array of per-(co,quarter) results). Only values that
ALREADY passed the sqrt(V'MV)≈item19 (status RECOVERED) or derive_irr≈item36
(irrStatus ok) gates in the workflow are stored — this script does not re-judge,
it just materialises validated cells.

- 36-40 stored from `found` (백만원 → 억원 /100) when status == RECOVERED, OR item36
  alone when irrStatus == ok (IRR-validated 금리위험액).
- 41-46 stored from `irr` (백만원 → 억원) when irrStatus == ok.
- Never overwrites an existing (code,item,quarter); appends only missing cells.

Usage: python scripts/apply_market_recovered.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from fill_market_subitems_to_disclosure import _to_eok, _meta_for, IRR_SCEN  # noqa: E402

JSON_PATH = REPO / "kics_disclosure.json"
RESULTS = REPO / "artifacts" / "kics_validation" / "wf_results.json"

SUB_NAMES = {36: "3-1. 금리위험액", 37: "3-2. 주식위험액", 38: "3-3. 부동산위험액",
             39: "3-4. 외환위험액", 40: "3-5. 자산집중위험액"}
IRR_NAMES = dict(IRR_SCEN)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--results", default=str(RESULTS))
    args = ap.parse_args(argv)

    results = json.loads(Path(args.results).read_text(encoding="utf-8"))
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    existing = {(r["원보험사코드"], int(r["항목번호"]), r["공시분기"]) for r in rows}

    new_rows = []
    plan = {"sub_recovered": 0, "partial_reconcile": 0, "item36_irr": 0, "irr_scen": 0,
            "skip_dup": 0, "cells_cq": 0}
    touched_cq = set()

    def add(code, quarter, item, name, eok):
        key = (code, item, quarter)
        if key in existing or key in {(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in new_rows}:
            plan["skip_dup"] += 1
            return False
        meta = _meta_for(rows, code)
        if not meta:
            return False
        new_rows.append({**meta, "원보험사코드": code, "항목번호": item,
                         "항목명": name, "공시분기": quarter, "값": eok})
        touched_cq.add((code, quarter))
        return True

    for r in results:
        if not r:
            continue
        code, quarter = r["code"], r["quarter"]
        found = r.get("found") or {}
        status = r.get("status", "")
        irr_ok = r.get("irrStatus") == "ok"
        irr = r.get("irr")

        rel = r.get("rel", 999)
        nn = r.get("nonNull", 0)
        # PARTIAL but reconciles (rel<2%, >=3 present): missing 36-40 are genuinely
        # ~0 (small insurers w/o 부동산/자산집중 risk); the present + zeros reconcile
        # to item19, so store present values AND explicit 0 for the (verified-zero) rest.
        partial_reconcile = status.startswith("PARTIAL") and rel < 2 and nn >= 3
        if status == "RECOVERED" or partial_reconcile:
            for i in (36, 37, 38, 39, 40):
                v = found.get(str(i))
                eok = _to_eok(v, "백만원") if v is not None else "0"
                if add(code, quarter, i, SUB_NAMES[i], eok):
                    plan["sub_recovered" if status == "RECOVERED" else "partial_reconcile"] += 1
        elif irr_ok and found.get("36") is not None:
            # IRR-validated 금리위험액 even when 37-40 not broken out (partial-publication)
            if add(code, quarter, 36, SUB_NAMES[36], _to_eok(found["36"], "백만원")):
                plan["item36_irr"] += 1

        if irr_ok and irr and len(irr) == 6:
            for (item, name), v in zip(IRR_SCEN, irr):
                if v is not None and add(code, quarter, item, name, _to_eok(v, "백만원")):
                    plan["irr_scen"] += 1

    plan["cells_cq"] = len(touched_cq)
    print("=== apply plan ===")
    for k, v in plan.items():
        print(f"  {k}: {v}")
    print(f"  total new rows: {len(new_rows)}  across {len(touched_cq)} (co,quarter)")

    if args.dry_run:
        print("\n[dry-run] not written. sample new rows:")
        for nr in new_rows[:8]:
            print("  ", json.dumps(nr, ensure_ascii=False))
        return

    if new_rows:
        rows.extend(new_rows)
        JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nWROTE {len(new_rows)} rows -> kics_disclosure.json (total {len(rows)})")
    else:
        print("\nnothing to write.")


if __name__ == "__main__":
    main(sys.argv[1:])
