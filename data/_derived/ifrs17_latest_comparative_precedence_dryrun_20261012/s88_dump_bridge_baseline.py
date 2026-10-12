"""Read-only: dump data/_gold/pl_bridge_baseline.json entries (key, class, reason, route, lhs, diff, first_seen)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
d = json.loads((ROOT / "data/_gold/pl_bridge_baseline.json").read_text(encoding="utf-8"))
ent = d["entries"]
print("entries", len(ent))
for k, v in ent.items():
    print(k, "|", v.get("class"), "|", (v.get("reason") or "")[:230].replace("\n", " "), "| route", v.get("route"), "| lhs", v.get("lhs"), "diff", v.get("diff"))
