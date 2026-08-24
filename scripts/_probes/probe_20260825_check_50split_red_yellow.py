# -*- coding: utf-8 -*-
from __future__ import annotations
import json
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)


def main() -> None:
    from src.solvency.validation.kics_json_rules import run_validation
    from validate_kics_disclosure import _load_tfi_applicability

    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    res = run_validation(rows, tfi_applicability=_load_tfi_applicability())
    findings = res["findings"] if isinstance(res, dict) else res

    for x in findings:
        if not x["rule"].startswith("50_tfi_tier_split"):
            continue
        if x["status"] not in ("RED", "YELLOW"):
            continue
        print(f"{x['원보험사코드']} {x['공시분기']:<9} {x['rule']:<22} {x['status']:<6} diff={x.get('diff')}")
        print(f"   {x.get('detail','')}")
        print()


if __name__ == "__main__":
    main()
