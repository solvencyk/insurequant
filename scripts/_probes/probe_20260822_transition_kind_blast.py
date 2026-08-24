# -*- coding: utf-8 -*-
"""Read-only: how far would replacing _TRANSITION_KIND with the per-quarter
measured sidecar actually reach?

_TRANSITION_KIND is consumed at exactly ONE site: the self-mirror classification
inside _axis_eval_rates (validate_kics_disclosure.py ~line 1166) which splits
mirror cells into mir_non / mir_legit / suspect. Only axes with a non-None
_AXIS_TRANSITION_KIND actually gate on it. This measures the blast radius in
cells, not in adjectives.

2026-08-22 validation iter-5. Modifies nothing."""
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from validate_kics_disclosure import (  # noqa: E402
    _AXIS_TRANSITION_KIND, _TRANSITION_APPLIERS, _TRANSITION_KIND,
)

side = json.loads(
    (ROOT / "data/_derived/kics_transition_applicability.json").read_text(encoding="utf-8")
)
AXIS_OF = side["_meta"]["kind_to_registry_axis"]      # TAC->AC, TIR->IR, TER->EQ, TIRR->INT
srec = {(r["code"], r["quarter"]): r for r in side["records"]}
names = {r["code"]: r["name"] for r in side["records"]}

print("=== 1. which axes actually gate on _TRANSITION_KIND ===")
for ax, k in _AXIS_TRANSITION_KIND.items():
    print(f"  {ax:24s} kinds={k}  {'GATES' if k else '(None -> never suspect)'}")
print()

# per-quarter measured kind set
measured = {}
for (c, q), r in srec.items():
    ks = set()
    for kind, axis in AXIS_OF.items():
        if r.get(kind) == "O":
            ks.add(axis)
    measured[(c, q)] = ks

print("=== 2. registry (company, fixed) vs measured (company x quarter) ===")
rows = []
for (c, q), ks in sorted(measured.items()):
    reg = _TRANSITION_KIND.get(c, set())
    if ks != reg:
        rows.append((c, names.get(c, c), q, sorted(reg), sorted(ks)))
print(f"  mismatching buckets = {len(rows)} / {len(measured)}")
by_co = Counter(r[0] for r in rows)
print(f"  companies involved  = {len(by_co)}")
print()

print("=== 3. the two disagreement directions ===")
extra_meas = [r for r in rows if set(r[4]) - set(r[3])]      # measured has kinds registry lacks
extra_reg = [r for r in rows if set(r[3]) - set(r[4])]       # registry has kinds measured lacks
print(f"  measured O but registry silent : {len(extra_meas)} buckets")
print(f"  registry claims but measured X : {len(extra_reg)} buckets")
print()
print("  -- measured O / registry silent, grouped by company --")
g = defaultdict(list)
for c, n, q, reg, ks in extra_meas:
    g[(c, n, tuple(reg))].append((q, tuple(sorted(set(ks) - set(reg)))))
for (c, n, reg), qs in sorted(g.items()):
    kinds = sorted({k for _, ks in qs for k in ks})
    applier = "APPLIER" if c in _TRANSITION_APPLIERS else "non-applier"
    print(f"    {c} {n:20s} [{applier}] registry={list(reg)} "
          f"measured-extra={kinds} in {len(qs)}Q: {[q for q, _ in qs]}")
print()

print("=== 4. BLAST RADIUS: mirror cells whose verdict would flip ===")
records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
KEY_CODE, KEY_QUARTER, KEY_ITEM = "원보험사코드", "공시분기", "항목번호"
KEY_VALUE, KEY_VALUE_POST = "값", "값_적용후"


def _num(x):
    if x in (None, ""):
        return None
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


byq = defaultdict(dict)
for r in records:
    c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
    try:
        it = int(it)
    except (TypeError, ValueError):
        continue
    if c and q:
        byq[(c, q)][it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))

# the three gating axes and their item sets (target + inputs), from _axis_specs
AXES = {
    "R1_가용자본=기본+보완": ({"AC"}, [1, 2, 3]),
    "R2_순자산합": ({"AC"}, [4, 5, 6, 7, 8, 9, 10, 11]),
    "mmult17": ({"IR"}, [17, 29, 30, 31, 32, 33, 34, 35]),
}
total_flip = 0
for axis, (kinds, items) in AXES.items():
    flips = []
    n_mirror = 0
    for (c, q), m in byq.items():
        if any(m.get(x, (None, None))[1] is None for x in items):
            continue
        if not all(m.get(x, (None, None))[0] is not None
                   and m.get(x, (None, None))[0] == m.get(x, (None, None))[1]
                   for x in items):
            continue
        n_mirror += 1
        if c not in _TRANSITION_APPLIERS:
            reg_verdict = "mir_non"
        elif kinds & _TRANSITION_KIND.get(c, set()):
            reg_verdict = "suspect"
        else:
            reg_verdict = "mir_legit"
        ms = measured.get((c, q))
        if ms is None:
            new_verdict = "UNKNOWN"
        elif kinds & ms:
            new_verdict = "suspect"
        else:
            new_verdict = "mir_legit"
        if reg_verdict != new_verdict:
            flips.append((c, names.get(c, c), q, reg_verdict, new_verdict))
    print(f"  {axis:24s} mirror cells={n_mirror}  verdict flips={len(flips)}")
    for f in flips[:12]:
        print(f"      {f[0]} {f[1]:18s} {f[2]}  {f[3]} -> {f[4]}")
    if len(flips) > 12:
        print(f"      ... +{len(flips)-12} more")
    total_flip += len(flips)
print(f"  TOTAL cells whose classification would change = {total_flip}")
