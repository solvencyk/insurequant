"""Dump given item range for (code, quarter)."""
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
code, q = sys.argv[1], sys.argv[2]
lo, hi = int(sys.argv[3]), int(sys.argv[4])
sub = sorted([r for r in rows if r["원보험사코드"] == code and r["공시분기"] == q
              and lo <= int(r["항목번호"]) <= hi], key=lambda r: int(r["항목번호"]))
print(f"===== {code} {q} items {lo}-{hi} =====")
for r in sub:
    print(f"  {r['항목번호']:>2} {r['항목명'][:32]:<32} 전={r.get('값')!s:>12}  후={r.get('값_적용후')!s:>12}")
