#!/usr/bin/env python3
"""Validate root kics_disclosure.json against K-ICS JSON rules."""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solvency.validation.kics_json_rules import KEY_CODE, KEY_QUARTER, run_validation

SPOT_CODE = "KR0005"
SPOT_QUARTER = "2025.4Q"
SPOT_NAME_HINT = "\ud5d5\uad6d\ud654\uc7ac"


def _load_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"Expected list JSON at {path}")
    return data


def _top_offenders(findings: list[dict], status: str, limit: int = 10) -> list[dict]:
    rows = [f for f in findings if f.get("status") == status]
    rows.sort(key=lambda f: abs(float(f.get("diff") or 0.0)), reverse=True)
    return [
        {
            "rule": f.get("rule"),
            "code": f.get(KEY_CODE),
            "quarter": f.get(KEY_QUARTER),
            "diff": f.get("diff"),
        }
        for f in rows[:limit]
    ]


def main() -> int:
    src = ROOT / "kics_disclosure.json"
    records = _load_records(src)
    report = run_validation(records)
    findings = report.get("findings", [])

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "kics_validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"report_{ts}.json"
    report["source"] = str(src)
    report["generated_at"] = ts
    report["spot_check"] = {
        "code": SPOT_CODE,
        "quarter": SPOT_QUARTER,
        "name_hint": "헕국화재",
        "findings": [
            f
            for f in findings
            if f.get(KEY_CODE) == SPOT_CODE and f.get(KEY_QUARTER) == SPOT_QUARTER
        ],
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = report.get("summary", {})
    by_status = summary.get("by_status", {})
    red = int(by_status.get("RED", 0))
    yellow = int(by_status.get("YELLOW", 0))
    err = int(by_status.get("ERROR", 0))

    fail_by_rule = Counter(f.get("rule") for f in findings if f.get("status") == "RED")
    print(f"K-ICS validation report: {out_path}")
    print(
        f"Status counts: RED={red} YELLOW={yellow} GREEN={by_status.get('GREEN', 0)} "
        f"SKIP={by_status.get('SKIP', 0)} ERROR={err}"
    )
    print("RED failures by rule:")
    for rule_id, cnt in sorted(fail_by_rule.items(), key=lambda x: (-x[1], x[0])):
        print(f"  rule {rule_id}: {cnt}")
    print("Top RED offenders:")
    for row in _top_offenders(findings, "RED", limit=10):
        print(f"  rule {row['rule']} {row['code']} {row['quarter']} diff={row['diff']}")

    spot = report["spot_check"]["findings"]
    spot_red = [f for f in spot if f.get("status") == "RED"]
    print(
        f"Spot-check {SPOT_CODE} {SPOT_QUARTER} ({SPOT_NAME_HINT}): "
        f"{len(spot)} results, RED={len(spot_red)}"
    )
    for f in spot:
        if f.get("status") == "RED":
            print(
                f"  RED rule {f.get('rule')}: expected={f.get('expected')} "
                f"actual={f.get('actual')} diff={f.get('diff')}"
            )

    return 2 if red > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
