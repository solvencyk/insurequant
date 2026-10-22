"""Read-only: dump the separate-FS statement of changes in equity (자본변동표) of KR0073 filings: header + balance rows."""
import sys, re
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "data/_derived/kyobo_pl_restate_dryrun_20261021"))
import stmt_parse as sp
sys.path.insert(0, str(ROOT / "data/_derived/remaining_20261022/b_bs_ilp"))
from s4_bs_rows import filings
sys.stdout.reconfigure(encoding="utf-8")
OUT = ROOT / "data/_derived/remaining_20261022/b_bs_ilp"
for fy, path in filings().items():
    lines = sp.read_lines(str(path))
    secs = sp.sections(lines)
    if "sep_fs" not in secs: print(fy, "no sep_fs"); continue
    lo, hi = secs["sep_fs"]
    rows = sp.rows_in_range(lines, lo, hi)
    start = None
    for i, r in enumerate(rows):
        if r["cells"] and r["cells"][0][0].replace(" ", "") == "자본변동표":
            start = i; break
    txt = [f"file={path.relative_to(ROOT).as_posix()} soce_start_idx={start}"]
    if start is not None:
        for r in rows[start:start+160]:
            c = r["cells"]
            t = " | ".join(x for x, _ in c)
            lab = c[0][0] if c else ""
            if i == start or re.search(r"기초|기말|제 ?\d+|자본금|총계|자본변동표|단위|합계", t) or len(c) <= 2:
                txt.append(f"  L{c[0][1] if c else r['tr']}: {t}")
    (OUT / f"soce_rows_{fy}.txt").write_text("\n".join(txt), encoding="utf-8")
    print(fy, start, len(txt))
