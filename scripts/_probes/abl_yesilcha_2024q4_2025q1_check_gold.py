"""Inspect data/_gold/user_pl_cells.json for KR0070 (ABL) overrides, for
inbox/parser/20260829T1100Z__orchestrator__KR0070__fill_2024q4_2025q1_yesilcha.md.

Read-only. Prints every KR0070 override row so we can tell which item7 entries were computed
under the item6=0 assumption for 2024.4Q/2025.1Q (per the prior ticket's own note: overrides
for 2024.1-3Q/2025.1-3Q were touched in 68cc.../commit around 2026-08-28, with 2025.1Q left
UNCHANGED because item6 was still suppressed then).

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/abl_yesilcha_2024q4_2025q1_check_gold.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
GOLD = REPO / "data" / "_gold" / "user_pl_cells.json"

d = json.loads(GOLD.read_text(encoding="utf-8"))
rows = d["set"]
kr70 = [r for r in rows if r["원보험사코드"] == "KR0070"]
print(f"KR0070 override entries: {len(kr70)}\n")
for r in sorted(kr70, key=lambda r: (r["항목번호"], r["공시분기"])):
    print(f"item{r['항목번호']:<3d} {r['공시분기']:8s} 값={r['값']:>12,.2f}  was={r.get('was')}")
    note = r.get("note", "")
    print(f"    note: {note[:200]}")
    print()
