"""Read-only: every row of the FY2024 Q3 separate statement (label + all cells with line numbers), to see how '-' (zero) cells are printed."""
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "data" / "_derived" / "kyobo_pl_restate_dryrun_20261021"))
import stmt_lines as S  # noqa: E402
import stmt_parse as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
path = S.main_xml("FY2024_Q3")
lines = P.read_lines(path)
sec = P.sections(lines)
print("sections:", {k: v for k, v in sec.items()})
rows = P.rows_in_range(lines, *sec["sep_fs"])
for r in rows:
    if not r["cells"]:
        continue
    lab = r["cells"][0][0]
    cells = [f"{t}@{ln}" for t, ln in r["cells"][1:]]
    print(f"TR{r['tr']:>6d} {lab[:40]:40s} {cells}")
