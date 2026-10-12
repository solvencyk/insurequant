"""Read-only: print PL master rows for one company over a quarter range.
usage: s97_peek_pl_cell.py <KRcode> [q1,q2,...] [item1,item2,...]"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
code = sys.argv[1]
qs = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]
items = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[3] else list(range(1, 33))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
rows = [r for r in pl if r["원보험사코드"] == code]
names = {r["항목번호"]: r["항목명"] for r in rows}
print(code, rows[0]["원수사명"] if rows else "")
print(f"{'item':>4} {'name':<22}" + "".join(f"{q:>26}" for q in qs))
for it in items:
    cells = []
    for q in qs:
        v = [r for r in rows if r["항목번호"] == it and r["공시분기"] == q]
        if v:
            vq = v[0].get("값_당분기")
            cells.append(f"{v[0]['값']!s:>14}/{vq!s:>11}")
        else:
            cells.append(f"{'-':>26}")
    print(f"{it:>4} {str(names.get(it, ''))[:22]:<22}" + "".join(f"{c:>26}" for c in cells))
