"""Read-only: dump separate-FS balance sheet of every KR0073 filing with raw line numbers (multi-line TE cells via stmt_parse)."""
import sys, re, glob, json
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "data/_derived/kyobo_pl_restate_dryrun_20261021"))
import stmt_parse as sp
sys.stdout.reconfigure(encoding="utf-8")
OUT = ROOT / "data/_derived/remaining_20261022/b_bs_ilp"

def filings():
    res = {}
    for p in sorted(glob.glob(str(ROOT / "data/dart/FY*/raw/KR0073*/**/*.xml"), recursive=True)):
        pp = Path(p)
        if re.fullmatch(r"\d{14}\.xml", pp.name):
            fy = re.search(r"FY\d{4}_Q\d", p).group(0)
            res.setdefault(fy, pp)
    return res

def bs_rows(path):
    lines = sp.read_lines(str(path))
    secs = sp.sections(lines)
    lo, hi = secs["sep_fs"]
    rows = sp.rows_in_range(lines, lo, hi)
    out = []
    for r in rows:
        c = r["cells"]
        if not c: continue
        out.append((r["tr"], [t for t, _ in c], [l for _, l in c]))
        if c[0][0].replace(" ", "") == "부채와자본총계":
            break
    return out

if __name__ == "__main__":
    for fy, path in filings().items():
        rows = bs_rows(path)
        txt = [f"file={path.relative_to(ROOT).as_posix()}"]
        for tr, cells, lns in rows:
            txt.append(f"  L{lns[0]}: " + " | ".join(cells))
        (OUT / f"bs_rows_{fy}.txt").write_text("\n".join(txt), encoding="utf-8")
        print(fy, len(rows))
