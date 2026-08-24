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

MY30 = {
    ("KR0004","2025.1Q"),("KR0004","2025.2Q"),("KR0004","2025.4Q"),("KR0004","2026.1Q"),
    ("KR0068","2023.4Q"),("KR0068","2024.2Q"),("KR0068","2024.3Q"),
    ("KR0087","2023.2Q"),("KR0087","2025.1Q"),("KR0087","2025.4Q"),
    ("KR0100","2023.1Q"),("KR0009","2025.1Q"),
    ("KR0080","2024.4Q"),("KR0080","2025.1Q"),("KR0080","2025.2Q"),("KR0080","2025.3Q"),
    ("KR0080","2025.4Q"),("KR0080","2026.1Q"),
    ("KR0010","2024.1Q"),("KR0010","2024.3Q"),("KR0010","2025.3Q"),("KR0010","2025.4Q"),("KR0010","2026.1Q"),
    ("KR0005","2024.4Q"),
    ("KR1098","2024.2Q"),("KR1098","2024.3Q"),("KR1098","2024.4Q"),
    ("KR0097","2024.2Q"),
    ("KR0071","2024.4Q"),
    ("KR0087","2026.1Q"),
}


def main() -> None:
    from src.solvency.validation.kics_json_rules import run_validation
    from validate_kics_disclosure import _load_tfi_applicability

    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    res = run_validation(rows, tfi_applicability=_load_tfi_applicability())
    findings = res["findings"] if isinstance(res, dict) else res

    seen = set()
    status_count = {}
    for x in findings:
        key = (x["원보험사코드"], x["공시분기"])
        if key not in MY30:
            continue
        if not x["rule"].startswith("50_tfi_tier_split"):
            continue
        seen.add(key)
        st = x["status"]
        status_count[st] = status_count.get(st, 0) + 1
        marker = "" if st == "GREEN" else "  <-- NOT GREEN"
        print(f"{x['원보험사코드']} {x['공시분기']:<9} {x['rule']:<22} {st:<6} diff={x.get('diff')}{marker}")

    print(f"\nstatus tally: {status_count}")
    missing = MY30 - seen
    if missing:
        print(f"\n[WARN] {len(missing)} buckets from MY30 had NO 50_tfi_tier_split finding at all (both pre+post?): {sorted(missing)}")
    else:
        print("\nAll 30 buckets produced findings for this rule (pre+post = 60 findings expected).")


if __name__ == "__main__":
    main()
