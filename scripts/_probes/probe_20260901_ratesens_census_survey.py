"""Survey: for every 공시분기 in kics_disclosure.json, compare the company roster there
against kics_rate_sensitivity.json's roster for the same quarter. Read-only — informs the
design of a new coverage-census rule (expected population = kics_disclosure cohort).

Usage: PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
       scripts/_probes/probe_20260901_ratesens_census_survey.py
"""
from __future__ import annotations
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

disc = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
rs = json.loads((REPO / "kics_rate_sensitivity.json").read_text(encoding="utf-8"))

disc_codes = defaultdict(set)
disc_names = {}
for r in disc:
    disc_codes[r["공시분기"]].add(r["원보험사코드"])
    disc_names[r["원보험사코드"]] = r["원수사명"]

rs_codes = defaultdict(set)
for r in rs:
    rs_codes[r["공시분기"]].add(r["원보험사코드"])

all_q = sorted(set(disc_codes) | set(rs_codes))
print(f"{'quarter':10s} {'disc_n':7s} {'rs_n':6s} {'missing_n':10s}  missing_codes")
for q in all_q:
    d = disc_codes.get(q, set())
    s = rs_codes.get(q, set())
    missing = sorted(d - s)
    extra = sorted(s - d)
    tag = ""
    if extra:
        tag = f"  EXTRA(in rs not disc): {extra}"
    print(f"{q:10s} {len(d):7d} {len(s):6d} {len(missing):10d}  {missing}{tag}")

print()
print("=== per-quarter-parity (odd/even) rollup ===")
odd = [q for q in all_q if q.endswith(("1Q", "3Q"))]
even = [q for q in all_q if q.endswith(("2Q", "4Q"))]
for label, qs in (("ODD (1Q/3Q)", odd), ("EVEN (2Q/4Q)", even)):
    tot_d = sum(len(disc_codes.get(q, set())) for q in qs)
    tot_s = sum(len(rs_codes.get(q, set())) for q in qs)
    print(f"{label}: quarters={qs}")
    print(f"  total disc company-quarters={tot_d}  total rs company-quarters={tot_s}  "
          f"coverage={tot_s}/{tot_d} ({100*tot_s/tot_d:.1f}%)" if tot_d else "  n/a")

print()
print("=== per-company: which quarters they're missing from RS despite being in disclosure ===")
per_co_missing = defaultdict(list)
for q in all_q:
    for code in sorted(disc_codes.get(q, set()) - rs_codes.get(q, set())):
        per_co_missing[code].append(q)
for code, qs in sorted(per_co_missing.items()):
    print(f"  {code:8s} {disc_names.get(code, code):16s} missing in RS: {qs}")
