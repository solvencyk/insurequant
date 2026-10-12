"""Read-only: CSM blocks whose verdict is 최신 채택 / 조건부 / 후보 미검증 (key, current vector, latest vector, items)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE / "csm_block_verdicts.csv", encoding="utf-8-sig")))
ov = json.loads((HERE / "cand" / "csm_adopt_overlay.json").read_text(encoding="utf-8"))
print("adopt overlay blocks:", len(ov), sorted(ov))
for r in rows:
    if r["verdict"].startswith(("최신 채택", "후보 미검증")):
        print(r["verdict"], "|", r["kr"], r["name"][:8], r["quarter"], "<-", r["later_filing_q"], "rcept", r["later_rcept"], "| items", r["diff_items"], "| small_reclass_only", r["small_reclass_only"], "| ilp", r["ilp_3plus6"], r["ilp_agrees_current"], r["ilp_agrees_latest"])
        print("      cur", r["current"], "\n      lat", r["latest"], "\n      viol", r["current_violations"][:80], "->", r["latest_violations"][:80])
