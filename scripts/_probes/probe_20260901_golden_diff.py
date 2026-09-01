# -*- coding: utf-8 -*-
"""Diff run_validation's manifest (buckets/findings/by_status/by_rule) between the
pre-fix and post-fix kics_disclosure.json, to document exactly what the golden update
captures. Read-only against both files (post-fix = live master; pre-fix = scratch copy
from git HEAD)."""
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

BEFORE = Path(sys.argv[1])
AFTER = REPO / "kics_disclosure.json"


def summarize(path):
    records = json.loads(path.read_text(encoding="utf-8"))
    report = run_validation(records, source_has_breakdown=_scan_breakdown_presence(records),
                            tfi_applicability=_load_tfi_applicability())
    return report


rb = summarize(BEFORE)
ra = summarize(AFTER)

print(f"buckets: {rb['summary']['buckets']} -> {ra['summary']['buckets']}")
print(f"findings: {rb['summary']['findings']} -> {ra['summary']['findings']}")
print(f"by_status BEFORE: {rb['summary']['by_status']}")
print(f"by_status AFTER:  {ra['summary']['by_status']}")

# per (rule,status) diff
from collections import Counter
def key_counts(report):
    c = Counter()
    for f in report["findings"]:
        c[(str(f.get("rule")), f.get("status"))] += 1
    return c

cb, ca = key_counts(rb), key_counts(ra)
keys = sorted(set(cb) | set(ca))
print("\nper (rule,status) changes:")
for k in keys:
    if cb.get(k, 0) != ca.get(k, 0):
        print(f"  {k}: {cb.get(k,0)} -> {ca.get(k,0)}")

# which specific findings for our 3 companies changed status
def our_findings(report):
    return [(f.get("원보험사코드"), f.get("공시분기"), str(f.get("rule")), f.get("status"),
             f.get("diff"))
            for f in report["findings"]
            if f.get("원보험사코드") in ("KR0029", "KR0070", "KR0071")]

fb = {(c,q,r): (s,d) for c,q,r,s,d in our_findings(rb)}
fa = {(c,q,r): (s,d) for c,q,r,s,d in our_findings(ra)}
print("\nour-company (rule) status changes (KR0029/KR0070/KR0071):")
for k in sorted(set(fb) | set(fa)):
    if fb.get(k) != fa.get(k):
        print(f"  {k}: {fb.get(k)} -> {fa.get(k)}")
