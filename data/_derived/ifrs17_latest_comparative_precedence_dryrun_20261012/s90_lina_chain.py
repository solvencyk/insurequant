"""Read-only: Lina (KR0074) CSM chain in the master + the held rows file (old basis) for the 2023.1Q/2Q feasibility statement."""
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
rows = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
M = {(r["공시분기"], r["항목번호"]): r["값"] for r in rows if r["원보험사코드"] == "KR0074"}
L = {r["항목번호"]: r.get("항목명") for r in rows}
print("labels", {k: L[k] for k in sorted(L)})
for q in ("2022.4Q", "2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"):
    print(q, [M.get((q, i)) for i in range(1, 7)])
held = json.loads((ROOT / "data/_derived/csm_backfill_lina_20261011/held_rows_waterfall.json").read_text(encoding="utf-8"))
print(type(held), (list(held.keys())[:10] if isinstance(held, dict) else len(held)))
print(json.dumps(held, ensure_ascii=False)[:1800])
