# -*- coding: utf-8 -*-
"""Read-only: dump rule findings + master item values for the re-audit buckets."""
import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))
from solvency.validation.kics_json_rules import run_validation

TARGETS = [("KR0075", "2024.3Q"), ("KR0075", "2024.4Q"), ("KR0075", "2025.1Q"),
           ("KR0087", "2025.2Q"), ("KR0073", "2025.2Q")]

data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
r = run_validation(data)
print("SUMMARY:", json.dumps(r["summary"], ensure_ascii=False))
for c, p in TARGETS:
    print("=" * 110)
    print(f"## {c} {p}  — findings (status != GREEN)")
    for f in r["findings"]:
        if f.get("원보험사코드") == c and f.get("공시분기") == p and f.get("status") != "GREEN":
            print(" ", json.dumps(f, ensure_ascii=False, default=str))
