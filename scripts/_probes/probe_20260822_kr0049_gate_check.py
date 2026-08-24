# -*- coding: utf-8 -*-
"""Read-only: inspect the latest validate_kics_disclosure.py JSON report for KR0049 2024.3Q
findings on rules 47_tier2_census / 48_tier2_limit / 50_tfi_tier_split / 51_tfi_tier2_composition."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPORT_DIR = REPO / "artifacts" / "kics_validation"


def main() -> int:
    reports = sorted(REPORT_DIR.glob("report_*.json"))
    if not reports:
        print("no report found")
        return 1
    latest = reports[-1]
    print(f"report={latest.name}")
    data = json.loads(latest.read_text(encoding="utf-8"))
    findings = data.get("findings") if isinstance(data, dict) else data
    if findings is None:
        print("keys:", list(data.keys()) if isinstance(data, dict) else type(data))
        return 1
    rules_of_interest = {
        "47_tier2_census", "47_tier2_census_post",
        "48_tier2_limit", "48_tier2_limit_post",
        "50_tfi_tier_split", "50_tfi_tier_split_post",
        "51_tfi_tier2_composition", "51_tfi_tier2_composition_post",
        "3_tier2_composition", "3_tier2_composition_post",
        "2_tier1_bridge", "2_tier1_bridge_post",
    }
    hits = [f for f in findings if f.get("code") == "KR0049" and f.get("quarter") == "2024.3Q"]
    print(f"total findings for KR0049 2024.3Q: {len(hits)}")
    for f in hits:
        rule = f.get("rule")
        marker = " <=== TFI/TIER2" if rule in rules_of_interest else ""
        print(f"  rule={rule:35s} status={f.get('status'):6s} detail={f.get('detail', '')[:140]}{marker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
