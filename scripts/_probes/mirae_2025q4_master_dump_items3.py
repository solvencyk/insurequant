import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

for fn in ("PL_breakdown.json", "data/dart/viz/pl_breakdown_master.json"):
    p = ROOT / fn
    rows = json.loads(p.read_text(encoding="utf-8"))
    hits = [r for r in rows if r.get("원보험사코드") == "KR0079" and r.get("공시분기") == "2025.4Q"]
    print(f"\n=== {fn} ({len(rows)} rows, {len(hits)} hits) ===")
    for r in sorted(hits, key=lambda r: r.get("항목번호", 0)):
        print(f"  item{r.get('항목번호')}: {r.get('항목명')!r} = {r.get('값')}  (값_당분기={r.get('값_당분기')})")
