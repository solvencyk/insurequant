# -*- coding: utf-8 -*-
"""Read-only: per-company timeline of (TFI flag, 47/48/49 presence) for every
company that has at least one absent quarter. Tests whether TFI *within a company*
explains the on/off pattern, which the marginal contingency cannot.

2026-08-22 validation iter-5. Modifies nothing."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from solvency.validation.kics_json_rules import _group_records, TIER2_ITEMS  # noqa: E402

data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
records = data["records"] if isinstance(data, dict) and "records" in data else data
buckets = _group_records(records)

side = json.loads(
    (ROOT / "data/_derived/kics_transition_applicability.json").read_text(encoding="utf-8")
)
srec = {(r["code"], r["quarter"]): r for r in side["records"]}


def qkey(q):
    try:
        y, p = q.split(".")
        return int(y), int(p[0])
    except Exception:
        return (0, 0)


by_code = {}
for b in buckets:
    by_code.setdefault((b.code, b.name), []).append(b)

print("=== companies with >=1 absent quarter: timeline  quarter[TFI]=presence ===")
print("    presence: 3 = all three rows, 0 = none, 1/2 = partial")
print()
for (code, name), bs in sorted(by_code.items()):
    bs = sorted(bs, key=lambda b: qkey(b.quarter))
    ns = [sum(1 for i in TIER2_ITEMS if i in b.values) for b in bs]
    if not any(n == 0 for n in ns):
        continue
    cells = []
    for b, n in zip(bs, ns):
        r = srec.get((b.code, b.quarter))
        t = (r.get("TFI") if r else "?") or "?"
        t = {"O": "O", "X": "X", "NA": "N", "UNKNOWN": "u"}.get(t, "?")
        cells.append(f"{b.quarter}[{t}]={n}")
    print(f"{code} {name}")
    print("    " + "  ".join(cells))
    # per-company conditional table
    tab = {}
    for b, n in zip(bs, ns):
        r = srec.get((b.code, b.quarter))
        t = (r.get("TFI") if r else "<NO_KEY>") or "<NO_KEY>"
        tab.setdefault(t, [0, 0])
        tab[t][0 if n == 0 else 1] += 1
    parts = [f"TFI={t}: absent {v[0]} / present {v[1]}" for t, v in sorted(tab.items())]
    print("    " + " | ".join(parts))
    print()

print("=== GLOBAL conditional: among ABSENT buckets only, TFI distribution ===")
from collections import Counter
c_abs, c_pres = Counter(), Counter()
for b in buckets:
    r = srec.get((b.code, b.quarter))
    t = (r.get("TFI") if r else "<NO_KEY>") or "<NO_KEY>"
    n = sum(1 for i in TIER2_ITEMS if i in b.values)
    (c_abs if n == 0 else c_pres)[t] += 1
print("  absent :", dict(c_abs))
print("  present:", dict(c_pres))
print()
print("  P(absent | TFI=X) =", f"{c_abs['X']}/{c_abs['X']+c_pres['X']}",
      f"= {c_abs['X']/(c_abs['X']+c_pres['X']):.1%}")
print("  P(absent | TFI=O) =", f"{c_abs['O']}/{c_abs['O']+c_pres['O']}",
      f"= {c_abs['O']/(c_abs['O']+c_pres['O']):.1%}")
