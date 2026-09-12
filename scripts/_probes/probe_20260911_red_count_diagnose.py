# -*- coding: utf-8 -*-
"""Diagnose the RED=36 (validate_kics_disclosure.py console) vs RED=60
(tests/test_kics_rules_golden.py --update) discrepancy -- same live master,
same 16140-finding count, different RED tally. Figure out where they diverge."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

report = json.loads((ROOT / "artifacts/kics_validation/report_latest.json").read_text(encoding="utf-8"))
findings = report["findings"]
print(f"report_latest.json findings: {len(findings)}")
c = Counter(f.get("status") for f in findings)
print(f"report_latest.json by_status: {dict(c)}")

# now replicate the golden's _run() exactly
from solvency.validation.kics_json_rules import run_validation
from validate_kics_disclosure import (
    _load_life_subrisk_applicability,
    _load_tfi_applicability,
    _scan_breakdown_presence,
)

records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
rep2 = run_validation(records,
                      source_has_breakdown=_scan_breakdown_presence(records),
                      tfi_applicability=_load_tfi_applicability(),
                      life_subrisk_applicability=_load_life_subrisk_applicability())
f2 = rep2["findings"]
print(f"\ngolden-style run_validation() findings: {len(f2)}")
c2 = Counter(x.get("status") for x in f2)
print(f"golden-style by_status: {dict(c2)}")

# diff: find findings whose status differs between the two runs for the same key
def key(f):
    return (f.get("원보험사코드") or f.get("company_code"), f.get("공시분기") or f.get("quarter"),
            str(f.get("rule")), f.get("column") or "")

idx1 = {key(f): f.get("status") for f in findings}
idx2 = {key(f): f.get("status") for f in f2}
diff_keys = [k for k in idx2 if idx1.get(k) != idx2.get(k)]
print(f"\nkeys present in golden-style but differing status vs report_latest: {len(diff_keys)}")
for k in diff_keys[:30]:
    print(f"  {k}: report_latest={idx1.get(k)!r} golden={idx2.get(k)!r}")

only_in_2 = [k for k in idx2 if k not in idx1]
only_in_1 = [k for k in idx1 if k not in idx2]
print(f"\nkeys only in golden-style: {len(only_in_2)}")
print(f"keys only in report_latest: {len(only_in_1)}")
