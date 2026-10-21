"""Read-only: PL identities on the live vector vs the planned vector (live + pl_plan.json cells), per quarter."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
plan = json.loads((HERE / "pl_plan.json").read_text(encoding="utf-8"))["plan"]
root = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
cur = {}
for r in root:
    if r["원보험사코드"] == "KR0073":
        cur.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
new = {q: dict(v) for q, v in cur.items()}
for c in plan:
    new[c["quarter"]][c["item"]] = c["new"]

IDS = [
    ("20=1+17", lambda v: (v[20], v[1], v[17]), lambda a, b, c: a - (b + c)),
    ("22=20+21", lambda v: (v[22], v[20], v[21]), lambda a, b, c: a - (b + c)),
    ("24=22-23", lambda v: (v[24], v[22], v[23]), lambda a, b, c: a - (b - c)),
    ("31=24+25", lambda v: (v[31], v[24], v[25]), lambda a, b, c: a - (b + c)),
    ("17=18+19", lambda v: (v[17], v[18], v[19]), lambda a, b, c: a - (b + c)),
    ("25=26+27+28+29+30+32", lambda v: (v[25], sum((v[i] or 0) for i in (26, 27, 28, 29, 30, 32)), 0), lambda a, b, c: a - b),
    ("1=2+15-16", lambda v: (v[1], v[2], (v[15] or 0) - (v[16] or 0)), lambda a, b, c: a - (b + c)),
    ("2=3+8", lambda v: (v[2], v[3], v[8]), lambda a, b, c: a - (b + c)),
    ("3=4+5+6+7", lambda v: (v[3], sum((v[i] or 0) for i in (4, 5, 6, 7)), 0), lambda a, b, c: a - b),
    ("8=9+10+11+12", lambda v: (v[8], sum((v[i] or 0) for i in (9, 10, 11, 12)), 0), lambda a, b, c: a - b),
]
NEEDS = {
    "20=1+17": (20, 1, 17), "22=20+21": (22, 20, 21), "24=22-23": (24, 22, 23), "31=24+25": (31, 24, 25), "17=18+19": (17, 18, 19),
    "25=26+27+28+29+30+32": (25, 26, 27, 28, 29, 30, 32), "1=2+15-16": (1, 2, 15, 16), "2=3+8": (2, 3, 8),
    "3=4+5+6+7": (3, 4, 5, 6, 7), "8=9+10+11+12": (8, 9, 10, 11, 12),
}
qs = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"]
print(f"{'identity':24s}" + "".join(f"{q + ' old/new':>26s}" for q in qs))
allok = True
for name, getter, fn in IDS:
    row = f"{name:24s}"
    for q in qs:
        cells = []
        for label, vec in (("old", cur[q]), ("new", new[q])):
            if any(vec.get(i) is None for i in NEEDS[name] if i not in (15, 16, 26, 27, 28, 29, 30, 32, 5, 6, 7, 9, 10, 11, 12)):
                cells.append("skip")
                continue
            try:
                a, b, c = getter({k: vec.get(k) for k in range(1, 33)})
                if a is None or b is None or c is None:
                    cells.append("skip")
                else:
                    cells.append(f"{fn(a, b, c):+.3f}")
            except TypeError:
                cells.append("skip")
        if cells[1] not in ("skip",) and abs(float(cells[1])) > 0.01:
            allok = False
        row += f"{cells[0] + ' / ' + cells[1]:>26s}"
    print(row)
print("ALL PLANNED-VECTOR IDENTITIES CLOSE (|residual| <= 0.01 백만원):", allok)
