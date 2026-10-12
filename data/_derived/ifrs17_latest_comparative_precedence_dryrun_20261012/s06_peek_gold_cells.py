"""Read-only: print gold-overlay cells (CSM or PL) for a company code (+ optional quarter).

usage: python s06_peek_gold_cells.py <csm|pl> <KR code> [quarter]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
which, code = sys.argv[1], sys.argv[2]
q = sys.argv[3] if len(sys.argv) > 3 else None
p = ROOT / "data/_gold" / ("user_csm_cells.json" if which == "csm" else "user_pl_cells.json")
d = json.loads(p.read_text(encoding="utf-8"))
n = 0
for c in d["set"]:
    if c.get("원보험사코드") != code:
        continue
    if q and c.get("공시분기") != q:
        continue
    print(json.dumps(c, ensure_ascii=False)[:1500])
    n += 1
print("cells", n)
