"""probe_cells.py (parser-kics, ticket 20261012T1030Z) -- READ ONLY.
Prints the current master cells (kics_disclosure.json) for the three buckets this ticket touches:
  KR1107 (Pacific Life Re) 2025.3Q / 2026.2Q items 1, 14, 27, 28, 47-54
  KR1101 (Munich Re)       2026.2Q items 1, 14, 47-54
  KR0049 (AXA)             2024.3Q items 3, 4, 27
usage: probe_cells.py
"""
import io
import json
import sys
from pathlib import Path

REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
print("rows:", len(rows))

WANT = [
    ("KR1107", "2025.3Q", list(range(1, 29)) + list(range(47, 55))),
    ("KR1107", "2026.2Q", list(range(1, 29)) + list(range(47, 55))),
    ("KR1101", "2026.2Q", [1, 2, 3, 14, 27, 28] + list(range(47, 55))),
    ("KR0049", "2024.3Q", [1, 2, 3, 4, 14, 15, 22, 23, 27, 28]),
]
idx = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in rows}
for code, q, items in WANT:
    print(f"\n== {code} {q}")
    for it in items:
        r = idx.get((code, q, it))
        if r is None:
            print(f"  item {it:>2}: <no row>")
        else:
            print(f"  item {it:>2}: 값={r['값']!r:>12}  값_적용후={r.get('값_적용후','<absent>')!r:>12}  | {r['항목명']}")
