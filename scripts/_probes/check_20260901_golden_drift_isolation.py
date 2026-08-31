# -*- coding: utf-8 -*-
"""In-process isolation: does this session's KR0005 item15/16/22 edit change the
tests/test_kics_rules_golden.py hash, independent of any OTHER concurrent drift?

Runs run_validation() twice -- once over the session-start backup (pre-fix), once over the
live kics_disclosure.json (post-fix, may also carry unrelated concurrent-session edits e.g.
KR0094 items 41-46) -- entirely in memory. Never writes to kics_disclosure.json.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from solvency.validation.kics_json_rules import run_validation  # noqa: E402
from validate_kics_disclosure import _load_tfi_applicability, _scan_breakdown_presence  # noqa: E402

BACKUP = REPO / "kics_disclosure.json.bak_20260901_035527_kr0005_combined_after"
LIVE = REPO / "kics_disclosure.json"
GOLDEN = REPO / "tests" / "fixtures" / "kics_rules_golden.json"


def manifest(path: Path) -> dict:
    records = json.loads(path.read_text(encoding="utf-8"))
    report = run_validation(records,
                             source_has_breakdown=_scan_breakdown_presence(records),
                             tfi_applicability=_load_tfi_applicability())
    findings = report["findings"]
    by_rule: dict = {}
    for f in findings:
        by_rule.setdefault(f["rule"], {}).setdefault(f["status"], 0)
        by_rule[f["rule"]][f["status"]] += 1
    payload = json.dumps(findings, sort_keys=True, default=str).encode()
    return {"sha256": hashlib.sha256(payload).hexdigest(), "by_rule": by_rule, "n": len(findings)}


m_pre = manifest(BACKUP)
m_post = manifest(LIVE)
golden = json.loads(GOLDEN.read_text(encoding="utf-8"))

print("golden sha256      :", golden.get("sha256"))
print("pre-fix (backup) sha:", m_pre["sha256"])
print("post-fix (live)  sha:", m_post["sha256"])
print()
print("pre-fix  == golden ?", m_pre["sha256"] == golden.get("sha256"))
print("post-fix == golden ?", m_post["sha256"] == golden.get("sha256"))
print("pre-fix  == post-fix (i.e. did MY edit change the rule-engine hash at all) ?",
      m_pre["sha256"] == m_post["sha256"])

if m_pre["sha256"] != m_post["sha256"]:
    print("\n--- by_rule diff (pre -> post) ---")
    rules = set(m_pre["by_rule"]) | set(m_post["by_rule"])
    for r in sorted(rules):
        a, b = m_pre["by_rule"].get(r), m_post["by_rule"].get(r)
        if a != b:
            print(f"  {r}: {a} -> {b}")
