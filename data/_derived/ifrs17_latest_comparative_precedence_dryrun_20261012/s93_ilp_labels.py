"""Read-only: ILP master item labels (1..16) and Lina KR0074 chain + restated sidecar entries."""
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
ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
L = {}
for r in ilp:
    L.setdefault(r["항목번호"], r.get("항목명"))
print({k: L[k] for k in sorted(L)})
M = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in ilp}
for kr in sys.argv[1:] or ["KR0074"]:
    for it in (9, 10, 11, 12, 13, 14, 15):
        print(kr, it, L.get(it), [(q, M.get((kr, q, it))) for q in ("2022.4Q", "2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q")])
side = json.loads((ROOT / "data/_derived/ilp_restated_comparative.json").read_text(encoding="utf-8"))
print(type(side), list(side.keys())[:6] if isinstance(side, dict) else len(side))
print(json.dumps(side, ensure_ascii=False)[:1800])
