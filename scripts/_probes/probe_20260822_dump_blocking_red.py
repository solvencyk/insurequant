# -*- coding: utf-8 -*-
"""Read-only: dump every blocking-RED finding for the tier2 axes with full detail text.
2026-08-22 parser-kics iter-4 investigation. Does not modify anything."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from solvency.validation.kics_json_rules import run_validation  # noqa: E402

data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
records = data["records"] if isinstance(data, dict) and "records" in data else data

result = run_validation(records, tolerance=2.0)
findings = result["findings"]

BLOCKING = {"2_tier1_bridge", "3_tier2_composition", "47_tier2_census", "47_tier2_census_post"}

reds = [f for f in findings if f.get("status") == "RED" and f.get("rule") in BLOCKING]
print(f"Total blocking RED (tier2 axes): {len(reds)}")
for f in sorted(reds, key=lambda x: (x["rule"], x.get("원보험사코드", ""), x.get("공시분기", ""))):
    print("---")
    print(f"rule={f['rule']} code={f.get('원보험사코드')} name={f.get('원수사명')} quarter={f.get('공시분기')}")
    print(f"expected={f.get('expected')} actual={f.get('actual')} diff={f.get('diff')}")
    print(f"detail={f.get('detail')}")
