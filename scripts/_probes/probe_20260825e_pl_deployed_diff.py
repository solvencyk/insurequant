# -*- coding: utf-8 -*-
"""PL_breakdown.json (배포본) build_pl() 실행 전/후 combo-diff (read-only)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\2e98dd9e-be51-411e-a455-ce573b8bf95c\scratchpad"
)
sys.stdout.reconfigure(encoding="utf-8")

before = json.loads((SCRATCH / "PL_breakdown.json.before").read_text(encoding="utf-8"))
after = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
print("before rows:", len(before), " after rows:", len(after))


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


b = {key(r): r for r in before}
a = {key(r): r for r in after}
print("keys only in before (dropped):", len(set(b) - set(a)))
print("keys only in after (added):", len(set(a) - set(b)))

changed = []
for k in set(b) & set(a):
    for f in ("값", "값_당분기"):
        bv, av = b[k].get(f), a[k].get(f)
        if bv != av:
            changed.append((k, f, bv, av))
print("changed cells (값/값_당분기):", len(changed))
for k, f, bv, av in sorted(changed):
    print(" ", k, f, bv, "->", av)

# Full-row diff (all fields, not just 값/값_당분기) for extra safety.
full_diff = []
for k in set(b) & set(a):
    if b[k] != a[k]:
        full_diff.append(k)
print("\nfull-row diffs (any field):", len(full_diff))
for k in full_diff:
    print("  ", k)
    print("    before:", b[k])
    print("    after :", a[k])
