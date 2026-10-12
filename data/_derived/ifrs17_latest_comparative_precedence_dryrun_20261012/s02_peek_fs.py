"""Read-only: peek at one FS-API cache file (rows + keys)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
p = ROOT / "data" / "dart" / "_fs_api_cache" / (sys.argv[1] if len(sys.argv) > 1 else "00103176_2024_11012_OFS.json")
d = json.loads(p.read_text(encoding="utf-8"))
print({k: (type(v).__name__, len(v) if hasattr(v, "__len__") else v) for k, v in d.items()})
rows = d.get("list") or []
print("rows", len(rows))
if rows:
    print("keys", list(rows[0].keys()))
    for r in rows[:6]:
        print(r)
    sj = {}
    for r in rows:
        sj[r.get("sj_nm")] = sj.get(r.get("sj_nm"), 0) + 1
    print(sj)
