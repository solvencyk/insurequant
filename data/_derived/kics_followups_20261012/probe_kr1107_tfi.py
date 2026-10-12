"""probe_kr1107_tfi.py (parser-kics, ticket 20261012T1030Z) -- READ ONLY.
Master state of KR1107 items 47-54 for every quarter (values, key presence, file position) + where a new block would be inserted.
usage: probe_kr1107_tfi.py [CODE]    (default KR1107)
"""
import io
import json
import sys
from pathlib import Path

REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
code = sys.argv[1] if len(sys.argv) > 1 else "KR1107"

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
qs = sorted({r["공시분기"] for r in rows if r["원보험사코드"] == code})
print(code, "quarters in master:", qs)
for q in qs:
    blk = [(i, r) for i, r in enumerate(rows) if r["원보험사코드"] == code and r["공시분기"] == q and 47 <= r["항목번호"] <= 54]
    if not blk:
        print(f"  {q}: no 47-54 rows")
        continue
    pos = [i for i, _ in blk]
    cells = []
    for _, r in blk:
        post = r["값_적용후"] if "값_적용후" in r else "<nokey>"
        cells.append(f"{r['항목번호']}:{r['값']}/{post}")
    print(f"  {q}: file idx {pos[0]}..{pos[-1]} contiguous={pos == list(range(pos[0], pos[-1] + 1))} | " + "  ".join(cells))

# ordering context: the file index range of this company's rows, and which item numbers sit right before / after the 47-54 blocks
print("\nneighbour rows around each 47-54 block (item numbers of previous / next row in file):")
for q in qs:
    blk = [i for i, r in enumerate(rows) if r["원보험사코드"] == code and r["공시분기"] == q and 47 <= r["항목번호"] <= 54]
    if blk:
        b0, b1 = blk[0], blk[-1]
        pr, nx = rows[b0 - 1], rows[b1 + 1]
        print(f"  {q}: prev=({pr['원보험사코드']},{pr['공시분기']},{pr['항목번호']}) next=({nx['원보험사코드']},{nx['공시분기']},{nx['항목번호']})")
