"""Full before/after diff census of root PL_breakdown.json after build_pl() ran off the
2025.2Q/2025.3Q item6 surgical patch. Confirms: (a) row count unchanged, (b) company-code
census unchanged (no company silently dropped), (c) every changed cell is KR0079, and lists
them all so the diff is auditable, not just summarized.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

before = json.loads((ROOT / "PL_breakdown.json.snapshot_pre_build_20260829_mirae2q3q")
                     .read_text(encoding="utf-8"))
after = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))

print(f"before rows: {len(before)}  after rows: {len(after)}")

companies_before = sorted({r["원보험사코드"] for r in before})
companies_after = sorted({r["원보험사코드"] for r in after})
print(f"companies before: {len(companies_before)}  after: {len(companies_after)}  "
      f"identical set: {companies_before == companies_after}")

key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731
before_idx = {key(r): r for r in before}
after_idx = {key(r): r for r in after}

print(f"before keys: {len(before_idx)}  after keys: {len(after_idx)}  "
      f"key sets identical: {set(before_idx) == set(after_idx)}")

changed = []
for k in before_idx:
    b, a = before_idx[k], after_idx[k]
    if b.get("값") != a.get("값") or b.get("값_당분기") != a.get("값_당분기"):
        changed.append((k, b.get("값"), a.get("값"), b.get("값_당분기"), a.get("값_당분기")))

print(f"\nchanged cells: {len(changed)}")
non_kr0079 = [c for c in changed if c[0][0] != "KR0079"]
print(f"non-KR0079 changed cells: {len(non_kr0079)}")
for c in changed:
    print(" ", c)
