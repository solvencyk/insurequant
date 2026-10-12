"""Read-only: CSM block verdict rows (csm_block_verdicts.csv) for the given company codes (all non-trivial rows + a count of the rest).
usage: python s96_show_csm_verdicts.py KR0073 KR0104 ..."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE / "csm_block_verdicts.csv", encoding="utf-8-sig")))
want = set(sys.argv[1:])
print("all rows", len(rows), dict(Counter(r["verdict"] for r in rows)))
for r in rows:
    if r["kr"] in want and r["verdict"] not in ("변화 없음",):
        print(r["kr"], r["name"][:8], r["quarter"], "<-", r["later_filing_q"], "|", r["scan_status"], r["fidelity"], r["tier"], "| items", r["diff_items"], "| gold", r["gold_cells"], "| viol", r["current_violations"][:60], "->", r["latest_violations"][:60], "|", r["verdict"], "|", r["note"][:90])
