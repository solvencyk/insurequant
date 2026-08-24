"""Read-only: survey the raw string formatting convention for KR0097 items
29-35 '값_적용후' across all quarters (precision, zero representation,
presence/absence of the key) so the fix uses a consistent format."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scratch_fmt_survey.txt"

data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
rows = data["rows"] if isinstance(data, dict) and "rows" in data else data

lines = []
by_q = {}
for r in rows:
    if r.get("원보험사코드") != "KR0097":
        continue
    n = int(r.get("항목번호", -1))
    if n not in range(29, 36):
        continue
    by_q.setdefault(r["공시분기"], {})[n] = r

for q in sorted(by_q):
    row = by_q[q]
    parts = []
    for n in range(29, 36):
        r = row.get(n)
        if r is None:
            parts.append(f"i{n}:MISSING_ROW")
            continue
        has_post = "값_적용후" in r
        post_repr = repr(r.get("값_적용후")) if has_post else "<no key>"
        parts.append(f"i{n} pre={r.get('값')!r} post={post_repr}")
    lines.append(f"{q}: " + " | ".join(parts))

out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out_path}")
