# -*- coding: utf-8 -*-
"""Read-only: compare the per-(company,quarter) O/X applicability facts in
data/_derived/kics_transition_applicability.json against the company-level,
time-invariant _TRANSITION_KIND registry in scripts/validate_kics_disclosure.py
(imported, never retyped). Lists every (company, quarter, kind) where the
observed value disagrees with what the registry implies. Does not modify
validate_kics_disclosure.py or the registry.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from validate_kics_disclosure import _TRANSITION_KIND, _TRANSITION_APPLIERS  # noqa: E402

KIND_TO_AXIS = {"TAC": "AC", "TIR": "IR", "TER": "EQ", "TIRR": "INT"}

REPO = Path(__file__).resolve().parents[2]
data = json.loads((REPO / "data/_derived/kics_transition_applicability.json").read_text(encoding="utf-8"))

mismatches = []
unregistered_but_active = defaultdict(set)  # code not in _TRANSITION_APPLIERS but shows some elective O
registered_but_never_o = defaultdict(lambda: defaultdict(lambda: {"O": 0, "X": 0, "NA": 0, "UNKNOWN": 0}))

for r in data["records"]:
    code, quarter = r["code"], r["quarter"]
    for kind, axis in KIND_TO_AXIS.items():
        val = r.get(kind, "UNKNOWN")
        registered = axis in _TRANSITION_KIND.get(code, set())
        registered_but_never_o[code][kind][val] += 1
        if val == "UNKNOWN":
            continue
        expect_o = registered
        observed_o = (val == "O")
        if expect_o != observed_o:
            mismatches.append((code, r["name"], quarter, kind, axis, val, "registered" if registered else "NOT_registered"))
        if observed_o and code not in _TRANSITION_APPLIERS:
            unregistered_but_active[code].add(kind)

print(f"=== _TRANSITION_KIND registry mismatches: {len(mismatches)} (code, quarter, kind) triples ===\n")
by_code = defaultdict(list)
for m in mismatches:
    by_code[m[0]].append(m)
for code in sorted(by_code):
    name = by_code[code][0][1]
    reg = _TRANSITION_KIND.get(code, set())
    print(f"{code} {name}  registry={sorted(reg)}  applier={code in _TRANSITION_APPLIERS}")
    for _, _, quarter, kind, axis, val, regstatus in sorted(by_code[code], key=lambda x: (x[3], x[2])):
        print(f"   {quarter:8s} {kind}({axis}) observed={val}  registry={regstatus}")
    print()

print(f"\n=== companies showing an elective O but NOT in _TRANSITION_APPLIERS (18-company frozenset): "
      f"{len(unregistered_but_active)} ===")
for code, kinds in sorted(unregistered_but_active.items()):
    name = next(r["name"] for r in data["records"] if r["code"] == code)
    print(f"  {code} {name}: kinds observed O = {sorted(kinds)}")

print(f"\n=== registered companies (frozenset+registry) whose registered axis NEVER shows O "
      f"across all resolved quarters (0 O, some X and/or UNKNOWN) ===")
for code, kindmap in sorted(registered_but_never_o.items()):
    reg = _TRANSITION_KIND.get(code, set())
    for kind, axis in KIND_TO_AXIS.items():
        if axis in reg:
            counts = kindmap[kind]
            if counts["O"] == 0 and (counts["X"] > 0 or counts["UNKNOWN"] > 0):
                name = next(r["name"] for r in data["records"] if r["code"] == code)
                print(f"  {code} {name} registry has {axis} but {kind} O={counts['O']} X={counts['X']} UNKNOWN={counts['UNKNOWN']}")
