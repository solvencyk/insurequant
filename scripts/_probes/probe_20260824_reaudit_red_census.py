# -*- coding: utf-8 -*-
"""Read-only: RED census from the rule engine vs what the gate reports.

Checks whether a RED that the rule engine emits for one of the re-audit buckets
(e.g. 19_market KR0003 2023.1Q) is counted by the gate or filtered somewhere else.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> None:
    from src.solvency.validation.kics_json_rules import run_validation
    from validate_kics_disclosure import _load_tfi_applicability

    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

    for label, kw in (("with tfi_applicability", {"tfi_applicability": _load_tfi_applicability()}),
                      ("bare (no tfi_applicability)", {})):
        res = run_validation(rows, **kw)
        fs = res["findings"] if isinstance(res, dict) else res
        reds = [f for f in fs if f["status"] == "RED"]
        print(f"\n=== {label}: findings={len(fs)}  RED={len(reds)} ===")
        for rule, n in sorted(Counter(f["rule"] for f in reds).items()):
            print(f"    {rule:<34} {n}")
        hit = [f for f in reds
               if f["원보험사코드"] == "KR0003" and f["공시분기"] == "2023.1Q"]
        print(f"    KR0003 2023.1Q REDs: {[f['rule'] for f in hit]}")


if __name__ == "__main__":
    main()
