# -*- coding: utf-8 -*-
import sys, io, json, importlib.util
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

spec = importlib.util.spec_from_file_location("validate_kics_disclosure", ROOT / "scripts" / "validate_kics_disclosure.py")
vmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vmod)

with open(ROOT / "kics_disclosure.json", "r", encoding="utf-8") as f:
    before = json.load(f)
with open(ROOT / "scripts" / "_probes" / "_scratch_kics_disclosure_KR0032test.json", "r", encoding="utf-8") as f:
    after = json.load(f)

for label, recs in (("BEFORE", before), ("AFTER", after)):
    red, review, pinned = vmod._post_transition_parent_census(recs)
    red_kr0032 = [x for x in red if x[0] == "KR0032" and x[1] == "2026.2Q"]
    review_kr0032 = [x for x in review if x[0] == "KR0032" and x[1] == "2026.2Q"]
    print(f"{label}: KR0032 2026.2Q core(RED) breaks = {red_kr0032}")
    print(f"{label}: KR0032 2026.2Q adjust(review) breaks = {review_kr0032}")

# also re-check 47_tier2_census RED offender line + overall exit-code-relevant totals via full report
before_report = vmod.run_validation(before, source_has_breakdown=vmod._scan_breakdown_presence(before),
                                     tfi_applicability=vmod._load_tfi_applicability())
after_report = vmod.run_validation(after, source_has_breakdown=vmod._scan_breakdown_presence(after),
                                    tfi_applicability=vmod._load_tfi_applicability())
print()
print("BEFORE summary keys sample:", {k: v for k, v in before_report.get("summary", {}).items() if isinstance(v, (int, float, str))})
print("AFTER summary keys sample:", {k: v for k, v in after_report.get("summary", {}).items() if isinstance(v, (int, float, str))})
