"""Read-only: dump the exact JSON record shape for KR0097 2024.4Q items 29-35,
and item17/item1 for cross-check, to a UTF-8 file (console is cp949)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scratch_kr0097_schema.txt"

data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
print(f"top-level type: {type(data)}", file=sys.stderr)
rows = data["rows"] if isinstance(data, dict) and "rows" in data else data
print(f"rows type: {type(rows)} len={len(rows) if hasattr(rows, '__len__') else 'n/a'}", file=sys.stderr)

lines = [f"top-level type: {type(data)}", f"is list: {isinstance(rows, list)}"]
if isinstance(rows, list):
    lines.append(f"n rows: {len(rows)}")

matches = [
    r for r in rows
    if r.get("원보험사코드") == "KR0097" and r.get("공시분기") == "2024.4Q"
    and int(r.get("항목번호", -1)) in (1, 17, 29, 30, 31, 32, 33, 34, 35)
]
matches.sort(key=lambda r: int(r.get("항목번호", 0)))
lines.append(f"n matches (Korean schema): {len(matches)}")
for r in matches:
    lines.append(json.dumps(r, ensure_ascii=False, sort_keys=True))

out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out_path}", file=sys.stderr)
