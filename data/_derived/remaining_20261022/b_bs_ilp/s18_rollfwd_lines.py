"""Read-only: locate the prior-year LRC/LIC roll-forward closing rows (restated) in the FY2024 annual separate notes with line numbers."""
import sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "data/_derived/kyobo_pl_restate_dryrun_20261021"))
import stmt_parse as sp
sys.stdout.reconfigure(encoding="utf-8")
p = ROOT / "data/dart/FY2024_Q4/raw/KR0073_교보생명보험_20250331004015/xml/20250331004015.xml"
lines = sp.read_lines(str(p))
secs = sp.sections(lines)
lo, hi = secs["sep_notes"]
rows = sp.rows_in_range(lines, lo, hi)
for i, r in enumerate(rows):
    c = [t for t, _ in r["cells"]]
    if "87,242,879" in c:
        ln = [l for _, l in r["cells"]]
        # find nearest preceding caption-like row
        cap = ""
        for j in range(i - 1, max(i - 40, 0), -1):
            cc = [t for t, _ in rows[j]["cells"]]
            if cc and ("구 분" in cc[0] or "구분" in cc[0] or "단위" in " ".join(cc)):
                cap = " | ".join(cc)[:150]; break
        print(f"L{ln[0]}: {' | '.join(c)[:230]}   <- hdr: {cap}")
