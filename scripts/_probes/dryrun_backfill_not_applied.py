"""Dry-run preview of backfill_post_transition_when_not_applied.py: show what
WOULD be filled without writing, broken out by (name, quarter)."""
from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backfill_post_transition_when_not_applied as m

ROOT = Path(__file__).resolve().parent.parent.parent
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

applying, safe_quarters = m.classify(data)
print(f"applying_companies: {sorted(applying)}")
print()

TARGETS = {"한화생명", "교보생명보험", "하나생명보험", "롯데손해보험", "농협생명보험"}

would_fill = Counter()
would_fill_items = {}
for r in data:
    if r.get("값_적용후") not in (None, ""):
        continue
    if r.get("값") in (None, ""):
        continue
    key = (r["원수사명"], r["공시분기"])
    if key not in safe_quarters:
        continue
    would_fill[key] += 1
    would_fill_items.setdefault(key, []).append(r["항목번호"])

print("=== 2026.1Q rows for target companies that WOULD be filled ===")
for (name, q), items in sorted(would_fill_items.items()):
    if name in TARGETS and q == "2026.1Q":
        print(f"{name} {q}: {sorted(items)} ({len(items)} cells)")

print()
print(f"TOTAL cells that would be filled across whole file: {sum(would_fill.values())}")
print(f"TOTAL (name,quarter) pairs touched: {len(would_fill)}")

print()
print("=== safe_quarters status for target companies, all quarters ===")
for name in sorted(TARGETS):
    is_applier = name in applying
    qs = sorted(q for (n, q) in safe_quarters if n == name)
    print(f"{name}: ever_applying={is_applier}, safe_quarters_count={len(qs)}")
