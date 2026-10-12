"""probe_axa_neighbors.py (parser-kics, ticket 20261012T1030Z) -- READ ONLY.
AXA (KR0049): master items 1, 2, 3, 4, 14, 27, 28 (값 / 값_적용후) for every quarter, to see which convention the master uses for the
headline ratio (printed 1-decimal vs derived item1/item14*100) and whether 값_적용후 mirrors 값 for items 2/3.
"""
import io
import json
import sys
from pathlib import Path

REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
idx = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in rows}
qs = sorted({r["공시분기"] for r in rows if r["원보험사코드"] == "KR0049"})
print("AXA quarters:", qs)
for it in (1, 2, 3, 4, 14, 27, 28):
    print(f"\n-- item {it}")
    for q in qs:
        r = idx.get(("KR0049", q, it))
        if r is None:
            print(f"   {q}: <no row>")
        else:
            print(f"   {q}: 값={r.get('값')!r:>16}  후={r.get('값_적용후', '<nokey>')!r:>16}")
