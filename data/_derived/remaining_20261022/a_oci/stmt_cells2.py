"""Read-only: print the OCI rows of the SEPARATE-basis comprehensive income statement of a KR0073 filing with raw line numbers per cell.
usage: stmt_cells2.py <FYdir> [lo hi]   (lo/hi = line range of the separate FS section; default from titles)"""
import re, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "data/_derived/kyobo_csm_basis_fix_20261021"))
sys.path.insert(0, str(ROOT / "data/_derived/kyobo_pl_restate_dryrun_20261021"))
from xmltab import parse_tables
import stmt_lines as SL
sys.stdout.reconfigure(encoding="utf-8")
fy = sys.argv[1]
path = SL.main_xml(fy)
tabs, titles = parse_tables(str(path))
s, e = SL.sep_range(titles)
if len(sys.argv) > 3:
    s, e = int(sys.argv[2]), int(sys.argv[3])
print("file", str(path.relative_to(ROOT)).replace("\\", "/"), "sep range", s, e)
KEY = re.compile("기타포괄|총포괄|순이익|재분류|평가손익|순금융손익|재측정|재평가|충당금|지분증권|손익")
for t in tabs:
    if not (s < t["start"] < e):
        continue
    labels = [r[1][0] for r in t["rows"] if r[1]]
    if any("영업이익" in x for x in labels) and any("순이익" in x for x in labels):
        print("TABLE", t["start"], t["end"], repr(t["caption"][:60]))
        for hr in t["header_rows"]:
            print("  HDR", hr)
        for ln, cells, cl in t["rows"]:
            if re.search(r"기타포괄|총포괄|순이익|재분류|평가손익|순금융손익|재측정|재평가|충당금|지분증권", cells[0]) and not re.search("이익$|수익$|손실$|관련", cells[0].strip()) or "순이익" in cells[0] or cells[0].strip() in ("기타포괄손익", "총포괄손익"):
                print(f"  rowL{ln} cells@{cl} {cells}")
        break
