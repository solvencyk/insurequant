"""Read-only: dump rows of the 소급재작성 효과 note (separate) of a Kyobo filing between two line numbers."""
import sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "data/_derived/kyobo_pl_restate_dryrun_20261021"))
import stmt_parse as sp
sys.stdout.reconfigure(encoding="utf-8")
path, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
lines = sp.read_lines(path)
# text paragraphs
for i in range(lo, hi + 1):
    ln = lines[i - 1]
    t = sp.clean(ln)
    if t and "<TD" not in ln and "<TE" not in ln and "<TH" not in ln and len(t) > 25:
        print(f"P L{i}: {t[:600]}")
rows = sp.rows_in_range(lines, lo, hi)
for r in rows:
    c = r["cells"]
    if c: print(f"  L{c[0][1]}: " + " | ".join(t for t, _ in c))
