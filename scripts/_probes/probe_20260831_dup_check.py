import json
import io
import sys
from collections import Counter
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
        counts = Counter(r.get("항목번호") for r in rows)
        dups = {k: v for k, v in counts.items() if v > 1}
        print(f"===== {code} {q}: n={len(rows)} unique_items={len(counts)} dups={dups} =====")
        if dups:
            for item_no in dups:
                for r in rows:
                    if r.get("항목번호") == item_no:
                        print(f"    dup item{item_no}: 항목명={r.get('항목명')!r} 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
        print("  items present:", sorted(counts.keys()))
        print()
