"""Read-only: print the separate-basis income statement rows (label + all numeric cells + last-cell line) of a filing."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stmt_parse as P
import stmt_lines as S
sys.stdout.reconfigure(encoding="utf-8")
fy = sys.argv[1]
path = S.main_xml(fy)
L = P.read_lines(path)
sec = P.sections(L)
lo, hi = sec["sep_fs"]
print(path.name, sec)
rows = P.rows_in_range(L, lo, hi)
start = None
for r in rows:
    if not r["cells"]:
        continue
    lab = r["cells"][0][0]
    if lab.replace(" ", "") in ("보험손익", "보험수익"):
        start = True
    if start:
        vals = [(c[0], c[1]) for c in r["cells"][1:]]
        nums = [P.num(v) for v, _ in vals]
        print(f"  L{r['cells'][-1][1]}: {lab[:34]:34s} {[ (v if len(v) < 22 else v[:22]) for v, _ in vals]}")
    if lab.replace(" ", "") in ("총포괄손익",) and start:
        break
