"""Read-only: (1) item x quarter pivot of the planned PL cells (old -> new), (2) the quarterly (당분기) cells that move because of the planned YTD changes.

Inputs : pl_cell_changes.csv, sim/cand_pl.json (real build_pl() simulation spliced into a copy of the live master), live PL_breakdown.json
Outputs: pl_before_after_pivot.txt, pl_quarterly_effect.txt
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"]

rows = list(csv.DictReader(open(HERE / "pl_cell_changes.csv", encoding="utf-8-sig")))
by = {(r["quarter"], int(r["item"])): r for r in rows}
names = {int(r["item"]): r["name"] for r in rows}


def f(x):
    return f"{float(x):,.0f}"


lines = ["항목 | " + " | ".join(QS), "---|" + "|".join(["---"] * len(QS))]
for it in range(1, 33):
    cells = []
    for q in QS:
        r = by.get((q, it))
        if r is None:
            cells.append("=")
        elif r["class"] == "FILL":
            cells.append(f"∅→{f(r['new'])}")
        else:
            cells.append(f"{f(r['old'])}→{f(r['new'])}")
    lines.append(f"{it} {names.get(it, '')} | " + " | ".join(cells))
(HERE / "pl_before_after_pivot.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))

live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
cand = json.loads((HERE / "sim" / "cand_pl.json").read_text(encoding="utf-8"))
k = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
lb = {k(r): r for r in live if r["원보험사코드"] == "KR0073"}
cb = {k(r): r for r in cand if r["원보험사코드"] == "KR0073"}
val_ch, q_ch = [], []
for key in lb:
    a, b = lb[key], cb[key]
    if a.get("값") != b.get("값"):
        val_ch.append(key)
    if a.get("값_당분기") != b.get("값_당분기"):
        q_ch.append(key)
only_q = [key for key in q_ch if key not in set(val_ch)]
out = [f"KR0073 cells with 값 changed: {len(val_ch)}; with 값_당분기 changed: {len(q_ch)}; 값_당분기 changed while 값 unchanged: {len(only_q)}"]
by_q = {}
for (_c, it, q) in only_q:
    by_q.setdefault(q, []).append(it)
for q in sorted(by_q):
    out.append(f"  derived-only 당분기 moves in {q}: items {sorted(by_q[q])}")
out.append("")
out.append("Quarterly (당분기) view of the headline items, old -> new (백만원):")
for it in (1, 4, 17, 24):
    for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"]:
        a, b = lb.get(("KR0073", it, q)), cb.get(("KR0073", it, q))
        if a is None:
            continue
        va, vb = a.get("값_당분기"), b.get("값_당분기")
        ya, yb = a.get("값"), b.get("값")
        out.append(f"  item{it:>2} {q}: 값(YTD) {ya if ya is None else f'{ya:,.0f}'} -> {yb if yb is None else f'{yb:,.0f}'} | 당분기 {va if va is None else f'{va:,.0f}'} -> {vb if vb is None else f'{vb:,.0f}'}")
(HERE / "pl_quarterly_effect.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
