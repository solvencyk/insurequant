# -*- coding: utf-8 -*-
"""Dump every RED finding for the 3 blocking tier2 axes from the latest
validate_kics_disclosure.py report, grouped by rule, with full detail text.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

RULES = {"2_tier1_bridge", "3_tier2_composition", "47_tier2_census",
         "2_tier1_bridge_post", "3_tier2_composition_post", "47_tier2_census_post"}


def main():
    report_path = sys.argv[1] if len(sys.argv) > 1 else None
    if report_path is None:
        cand = sorted((REPO / "artifacts" / "kics_validation").glob("report_*.json"))
        report_path = str(cand[-1])
    data = json.loads(Path(report_path).read_text(encoding="utf-8"))
    findings = data["findings"]
    print(f"report = {report_path}")
    by_rule: dict[str, list] = {}
    for f in findings:
        rule = f.get("rule")
        if rule in RULES and f.get("status") == "RED":
            by_rule.setdefault(rule, []).append(f)
    total = 0
    for rule in sorted(by_rule):
        items = by_rule[rule]
        total += len(items)
        print(f"\n===== {rule}  ({len(items)}건) =====")
        for f in items:
            print(f"  {f.get('원보험사코드')} {f.get('원수사명')} {f.get('공시분기')} "
                  f"expected={f.get('expected')} actual={f.get('actual')} diff={f.get('diff')}")
            print(f"    detail: {f.get('detail')}")
    print(f"\nTOTAL RED (tier2 axes) = {total}")


if __name__ == "__main__":
    raise SystemExit(main())
