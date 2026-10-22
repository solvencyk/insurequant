"""Read-only: closing-equity rows (반기말자본) of FY2026_Q2 xml around lines 5920 and 32013 (which one is the separate statement?)."""
import sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "data/_derived/kyobo_pl_restate_dryrun_20261021"))
import stmt_parse as sp
sys.stdout.reconfigure(encoding="utf-8")
p = ROOT / "data/dart/FY2026_Q2/raw/KR0073_교보생명보험/20260814004024.xml"
lines = sp.read_lines(str(p))
for tgt in (5920, 6268, 32013, 32233):
    rows = sp.rows_in_range(lines, tgt - 400, tgt + 60)
    for r in rows:
        c = r["cells"]
        if c and ("말자본" in c[0][0]):
            print(tgt, f"L{c[0][1]}:", " | ".join(t for t, _ in c))
# titles near
for i, ln in enumerate(lines, 1):
    if "<TITLE" in ln and ("재무제표" in ln or "연결" in ln):
        print("TITLE", i, sp.clean(ln)[:80])
