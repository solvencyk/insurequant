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
    out, pinned = vmod._parent_present_child_incomplete_after(recs)
    kr_hits = [x for x in out if x[0] == "KR0032" and x[1] == "2026.2Q"]
    print(f"{label}: KR0032 2026.2Q after_incomplete = {kr_hits}")
