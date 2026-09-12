# -*- coding: utf-8 -*-
"""Ticket 3: prove the stale-quarter detector is alive by running it against
the PRE-resubmission-fix master (commit 7c33aae, parent of 66cfa0b which
corrected KR0003 2026.1Q's item47-52) and confirming it still catches the
fingerprint -- then confirm the CURRENT master no longer trips it (data fixed,
not detector dead).
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_stale_quarter_tables.py"

spec = importlib.util.spec_from_file_location("_stale_quarter", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

OLD = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a58c26ac-9516-4250-9994-281cfa9a1766\scratchpad\kics_disclosure_prefix_7c33aae.json")
old_records = json.loads(OLD.read_text(encoding="utf-8"))
new_records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

print("=== detect() on PRE-fix master (commit 7c33aae, before 66cfa0b) ===")
old_hits = m.detect(old_records)
for h in old_hits:
    print(" ", h)

print()
print("=== detect() on CURRENT master ===")
new_hits = m.detect(new_records)
for h in new_hits:
    print(" ", h)
if not new_hits:
    print("  (no hits at all)")

# also show KR0003 2026.1Q item14/item48 in both snapshots for a human-readable diff
for label, recs in (("OLD(7c33aae)", old_records), ("NEW(current)", new_records)):
    by_item = {}
    for r in recs:
        if r["원보험사코드"] == "KR0003" and r["공시분기"] in ("2025.4Q", "2026.1Q") and int(r["항목번호"]) in (14, 47, 48, 49, 50, 51, 52):
            by_item.setdefault(r["공시분기"], {})[int(r["항목번호"])] = (r.get("값"), r.get("값_적용후"))
    print(f"\n{label}:")
    for q in ("2025.4Q", "2026.1Q"):
        print(f"  {q}: {by_item.get(q)}")
