import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

q = "2026.2Q"
rows27 = []
rows28 = []
for row in data:
    if row.get("공시분기") != q:
        continue
    if row.get("항목번호") == 27:
        rows27.append(row)
    elif row.get("항목번호") == 28:
        rows28.append(row)

print(f"item27 rows in {q}: {len(rows27)}")
for r in rows27[:20]:
    print(f"  {r.get('원보험사코드')} 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")

print(f"\nitem28 rows in {q}: {len(rows28)}")
for r in rows28[:25]:
    print(f"  {r.get('원보험사코드')} 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
