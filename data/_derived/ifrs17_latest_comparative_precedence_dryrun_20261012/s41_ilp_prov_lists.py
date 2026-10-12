"""Read-only: summarize ILP provenance not-loaded lists by reason."""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
d = json.loads((ROOT / "insurance_liability_portfolio_provenance.json").read_text(encoding="utf-8"))
print("not_loaded:")
for x in d["not_loaded"]:
    print("  ", json.dumps(x, ensure_ascii=False)[:400])
nl = d["lrc_model_not_loaded"]
print("lrc_model_not_loaded:", len(nl), "keys", list(nl[0].keys()))
by = defaultdict(list)
for x in nl:
    r = (x.get("reason") or x.get("why") or "")
    by[r[:110]].append((x.get("company_code"), x.get("quarter")))
for r, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
    cos = Counter(c for c, _ in v)
    print(f"  n={len(v):3d} reason={r!r}")
    print("        ", dict(cos), sorted({q for _, q in v})[:8])
print("resolved flags:", Counter(bool(x.get("resolved")) for x in nl))
print("sample:", json.dumps(nl[0], ensure_ascii=False)[:500])
