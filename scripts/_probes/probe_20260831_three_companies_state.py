import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

codes = ["KR0011", "KR0029", "KR0051"]
quarters = ["2026.1Q", "2026.2Q"]

by_key = {}
for row in data:
    code = row.get("원보험사코드")
    if code not in codes:
        continue
    q = row.get("공시분기")
    if q not in quarters:
        continue
    by_key.setdefault((code, q), []).append(row)

for code in codes:
    for q in quarters:
        rows = by_key.get((code, q), [])
        rows.sort(key=lambda r: r.get("항목번호", 0))
        print(f"===== {code} {q} ({len(rows)} rows) =====")
        for r in rows:
            item_no = r.get("항목번호")
            name = r.get("항목명")
            val = r.get("값")
            val_post = r.get("값_적용후", "<none>")
            print(f"  {item_no:>3} | {name!r:60s} | 값={val!r} | 값_적용후={val_post!r}")
        print()
