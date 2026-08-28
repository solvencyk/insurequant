"""Read-only snapshot of ALL current PL_breakdown.json items for KR0079 2025.4Q, to see what's
already populated (and therefore in scope for the "did the duplicate-shift bug contaminate other
cells" question) vs what's 0/blank. Read-only.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
d = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
rows = sorted(
    (r for r in d if r["원보험사코드"] == "KR0079" and r["공시분기"] == "2025.4Q"),
    key=lambda r: r["항목번호"],
)
print(f"KR0079 2025.4Q: {len(rows)} rows")
for r in rows:
    print(f"  item{r['항목번호']:>2} {r.get('항목명','')!s:30s} 값={r['값']!r}  값_당분기={r.get('값_당분기')!r}")
