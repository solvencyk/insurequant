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
    partial, full_absent = vmod._parent_present_child_incomplete(recs)
    partial_hit = [x for x in partial if x[0] == "KR0032" and x[1] == "2026.2Q"]
    full_hit = [x for x in full_absent if x[0] == "KR0032" and x[1] == "2026.2Q"]
    print(f"{label} partial_red (KR0032 2026.2Q): {partial_hit}")
    print(f"{label} full_absent_even_review (KR0032 2026.2Q): {full_hit}")

    pz = vmod._parent_zero_child_nonzero(recs)
    pz_hit = [x for x in pz if x[0] == "KR0032" and x[1] == "2026.2Q"]
    print(f"{label} parent_zero_child_nonzero (KR0032 2026.2Q): {pz_hit}")
    print()

# coverage census + exit-code path: replicate main()'s exit logic roughly
print("=== coverage census (regular filer completeness) ===")
for label, recs in (("BEFORE", before), ("AFTER", after)):
    census = vmod._coverage_census(recs)
    kr0032_missing = [m for m in census["missing_rows"] if m[1] == "KR0032"]
    print(f"{label}: KR0032 in missing_rows = {kr0032_missing}")
