#!/usr/bin/env python3
"""Golden gate for the K-ICS rule engine (run_validation).

run_validation is 393 lines — a 361-line per-bucket loop applying 14 rules
(1-10, 8_post, 8_life, 19_market, 36_irr) — and it had no unit test at all,
despite being the engine behind the RED count the push gate blocks on.

This pins its output on the live master: it runs the engine over
kics_disclosure.json exactly as scripts/validate_kics_disclosure.py does
(same source_has_breakdown input) and asserts a per-(rule,status) count
matrix plus a hash of the full finding list. No file is written; the engine
is pure. Fast (<1s), so it runs unconditionally.

If the counts legitimately change (a rule fix, new data), regenerate and say
why in the commit:

    python tests/test_kics_rules_golden.py --update
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

GOLDEN = REPO / "tests" / "fixtures" / "kics_rules_golden.json"
MASTER = REPO / "kics_disclosure.json"


def _run() -> dict:
    from solvency.validation.kics_json_rules import run_validation
    from validate_kics_disclosure import _scan_breakdown_presence

    records = json.loads(MASTER.read_text(encoding="utf-8"))
    report = run_validation(records, source_has_breakdown=_scan_breakdown_presence(records))
    return report


def _manifest(report: dict) -> dict:
    findings = report["findings"]
    # stable key per finding — (code, quarter, rule, status, diff bucketed)
    rows = []
    for f in findings:
        rows.append([
            f.get("company_code"), f.get("quarter"), str(f.get("rule")),
            f.get("status"),
        ])
    rows.sort(key=lambda r: (str(r[0]), str(r[1]), str(r[2])))
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    return {
        "sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "buckets": report["summary"]["buckets"],
        "findings": report["summary"]["findings"],
        "by_status": report["summary"]["by_status"],
        "by_rule": report["summary"]["by_rule"],
    }


def test_rule_engine_output_matches_golden():
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    actual = _manifest(_run())
    for k in ("sha256", "buckets", "findings", "by_status", "by_rule"):
        assert expected.get(k) == actual[k], (
            f"run_validation output moved at '{k}':\n"
            f"  expected: {expected.get(k)}\n  actual:   {actual[k]}\n"
            f"If intended, regenerate: python {GOLDEN.name} --update"
        )


def _update() -> int:
    man = _manifest(_run())
    man["_what"] = ("Refactor safety net for run_validation (K-ICS rule engine). "
                    "Captured before the 361-line per-bucket loop was extracted. "
                    "Covers every (code, quarter, rule, status) finding over the live "
                    "kics_disclosure.json.")
    GOLDEN.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {GOLDEN}: {man['findings']} findings / {man['buckets']} buckets")
    print(f"  by_status: {man['by_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_update() if "--update" in sys.argv else 0)
