# -*- coding: utf-8 -*-
"""Combo-diff CSM_waterfall.json before (backup) vs after (freshly rebuilt via
build_csm() only). Reports: row-count delta, non-null count delta, and a full list
of every (code, quarter, item) whose '값' or '값_당분기' changed, grouped by
company so an unexpected non-KR0079 company jumps out immediately.
"""
import sys, json
from pathlib import Path
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

before = json.loads((ROOT / "CSM_waterfall.json.bak_20260830_item45split").read_text(encoding="utf-8"))
after = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))

def key(r):
    return (r["원보험사코드"], r["공시분기"], r["항목번호"])

b_idx = {key(r): r for r in before}
a_idx = {key(r): r for r in after}

b_keys, a_keys = set(b_idx), set(a_idx)
lost = b_keys - a_keys
gained = a_keys - b_keys

lines = []
lines.append(f"before rows: {len(before)}  after rows: {len(after)}")
lines.append(f"lost keys (in before, not after): {len(lost)}")
lines.append(f"gained keys (in after, not before): {len(gained)}")
if lost:
    lines.append(f"  LOST SAMPLE: {sorted(lost)[:20]}")
if gained:
    lines.append(f"  GAINED SAMPLE: {sorted(gained)[:20]}")

# non-null census (per field), both files
for label, rows in (("before", before), ("after", after)):
    nn_val = sum(1 for r in rows if r.get("값") is not None)
    nn_dangi = sum(1 for r in rows if r.get("값_당분기") is not None)
    lines.append(f"{label}: non-null 값={nn_val}  non-null 값_당분기={nn_dangi}")

changed_by_company = defaultdict(list)
n_val_changes = 0
n_dangi_changes = 0
for k in sorted(b_keys & a_keys):
    br, ar = b_idx[k], a_idx[k]
    dv = br.get("값") != ar.get("값")
    dd = br.get("값_당분기") != ar.get("값_당분기")
    if dv or dd:
        code = k[0]
        changed_by_company[code].append((k, br.get("값"), ar.get("값"), br.get("값_당분기"), ar.get("값_당분기")))
        if dv:
            n_val_changes += 1
        if dd:
            n_dangi_changes += 1

lines.append(f"\ncell '값' changes: {n_val_changes}")
lines.append(f"cell '값_당분기' changes: {n_dangi_changes}")
lines.append(f"companies with ANY change: {sorted(changed_by_company.keys())}")

for code in sorted(changed_by_company):
    lines.append(f"\n=== {code} ({len(changed_by_company[code])} cells) ===")
    for k, bv, av, bd, ad in changed_by_company[code]:
        parts = [f"  {k[1]} item{k[2]}:"]
        if bv != av:
            parts.append(f" 값 {bv}->{av}")
        if bd != ad:
            parts.append(f" 당분기 {bd}->{ad}")
        lines.append("".join(parts))

# also: check every OTHER field for any drift (defensive — catch a field-level null-out
# that combo-diff on 값/값_당분기 alone would miss, per the "2-layer loss" caution)
all_fields = set()
for r in before + after:
    all_fields.update(r.keys())
field_drift = []
for k in sorted(b_keys & a_keys):
    br, ar = b_idx[k], a_idx[k]
    for f in sorted(all_fields):
        if f in ("값", "값_당분기"):
            continue
        if br.get(f) != ar.get(f):
            field_drift.append((k, f, br.get(f), ar.get(f)))
lines.append(f"\nother-field drift (excluding 값/값_당분기): {len(field_drift)}")
for k, f, bv, av in field_drift[:50]:
    lines.append(f"  {k} field={f}: {bv!r} -> {av!r}")

out = ROOT / "scripts/_probes/_out_20260830_item45_combo_diff.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print(f"\n...full report also at: {out}")
