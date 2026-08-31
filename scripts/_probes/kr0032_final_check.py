# -*- coding: utf-8 -*-
"""Run the real validate_kics_disclosure.run_validation in-process on BEFORE (live) and AFTER
(scratch-patched) records, diff KR0032 2026.2Q findings by rule/status, and print global RED deltas."""
import sys, io, json, importlib.util
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("validate_kics_disclosure", ROOT / "scripts" / "validate_kics_disclosure.py")
vmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vmod)

with open(ROOT / "kics_disclosure.json", "r", encoding="utf-8") as f:
    before_records = json.load(f)
with open(ROOT / "scripts" / "_probes" / "_scratch_kics_disclosure_KR0032test.json", "r", encoding="utf-8") as f:
    after_records = json.load(f)

before_report = vmod.run_validation(before_records,
                                     source_has_breakdown=vmod._scan_breakdown_presence(before_records),
                                     tfi_applicability=vmod._load_tfi_applicability())
after_report = vmod.run_validation(after_records,
                                    source_has_breakdown=vmod._scan_breakdown_presence(after_records),
                                    tfi_applicability=vmod._load_tfi_applicability())


def kr0032_findings(report):
    return {
        (f["rule"], f.get("status")): f
        for f in report["findings"]
        if f.get("원보험사코드") == "KR0032" and f.get("공시분기") == "2026.2Q"
    }


def by_rule(report):
    out = {}
    for f in report["findings"]:
        if f.get("원보험사코드") == "KR0032" and f.get("공시분기") == "2026.2Q":
            out[f["rule"]] = f
    return out


before_rules = by_rule(before_report)
after_rules = by_rule(after_report)

all_rules = sorted(set(before_rules) | set(after_rules))
print(f"{'rule':30s} {'before':>8s} {'after':>8s}   before_detail -> after_detail")
changed = []
for rule in all_rules:
    b = before_rules.get(rule)
    a = after_rules.get(rule)
    bs = b["status"] if b else "N/A"
    as_ = a["status"] if a else "N/A"
    marker = "  <-- CHANGED" if bs != as_ else ""
    if marker:
        changed.append((rule, bs, as_))
    print(f"{rule:30s} {bs:>8s} {as_:>8s}{marker}")

print()
print("=== Global RED counts ===")


def count_status(report, status):
    return sum(1 for f in report["findings"] if f.get("status") == status)


for status in ("RED", "YELLOW", "GREEN", "SKIP"):
    b = count_status(before_report, status)
    a = count_status(after_report, status)
    print(f"{status:8s} before={b:6d} after={a:6d} delta={a-b:+d}")

print()
print("=== structural gates (KR0032 2026.2Q related) ===")
for key in ("parent_zero_child_nonzero", "market_tooling_fail"):
    b_hits = [x for x in before_report.get(key, []) if x.get("code") == "KR0032"]
    a_hits = [x for x in after_report.get(key, []) if x.get("code") == "KR0032"]
    print(f"{key}: before={len(b_hits)} after={len(a_hits)}")

pci_b = before_report.get("parent_present_child_incomplete", {})
pci_a = after_report.get("parent_present_child_incomplete", {})
for sub in ("partial_red", "full_absent_even_review"):
    b_hits = [x for x in pci_b.get(sub, []) if x.get("code") == "KR0032"]
    a_hits = [x for x in pci_a.get(sub, []) if x.get("code") == "KR0032"]
    print(f"parent_present_child_incomplete.{sub}: before={len(b_hits)} after={len(a_hits)}  before={b_hits} after={a_hits}")

apmc_b = [x for x in before_report.get("after_parent_missing_child_present", []) if x.get("code") == "KR0032"]
apmc_a = [x for x in after_report.get("after_parent_missing_child_present", []) if x.get("code") == "KR0032"]
print(f"after_parent_missing_child_present: before={len(apmc_b)} after={len(apmc_a)}")

# transition continuity break (TRAILING) — find function name
for key in list(before_report.keys()):
    if "continu" in key.lower() or "trailing" in key.lower():
        print("candidate continuity key:", key)

print()
print(f"CHANGED rules ({len(changed)}):")
for rule, bs, as_ in changed:
    print(f"  {rule}: {bs} -> {as_}")

print()
print("=== full AFTER findings for KR0032 2026.2Q (all rules) ===")
for rule in sorted(after_rules):
    f = after_rules[rule]
    print(json.dumps(f, ensure_ascii=False))
