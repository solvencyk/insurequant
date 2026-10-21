"""Read-only: compact per-quarter before/after view of the planned PL cells (from pl_cell_changes.csv) + the quarterly (당분기) effect."""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(open(HERE / "pl_cell_changes.csv", encoding="utf-8-sig")))
by_q = {}
for r in rows:
    by_q.setdefault(r["quarter"], []).append(r)
f = lambda s: "∅" if s in ("", "None", None) else f"{float(s):,.0f}"
out = []
for q, rs in by_q.items():
    ch = [r for r in rs if r["class"] == "CHANGED"]
    fl = [r for r in rs if r["class"] == "FILL"]
    out.append(f"{q}: CHANGED {len(ch)} / FILL {len(fl)}   (from {rs[0]['later_filing'].split('/')[-1]})")
    out.append("   CHANGED: " + "; ".join(f"{r['item']}:{f(r['old'])}→{f(r['new'])}" for r in ch))
    if fl:
        out.append("   FILL   : " + "; ".join(f"{r['item']}:{f(r['new'])}" for r in fl))
text = "\n".join(out)
print(text)
(HERE / "pivot_changes.txt").write_text(text + "\n", encoding="utf-8", newline="\n")
