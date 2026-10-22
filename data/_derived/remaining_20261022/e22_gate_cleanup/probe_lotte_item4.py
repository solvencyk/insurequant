"""Read-only: confirm the cell behind LEDGER_INERT (롯데손해보험 2023.1Q) is genuinely filled, not just out of scope."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
for r in pl:
    if r["원수사명"] == "롯데손해보험" and r["공시분기"] == "2023.1Q" and r["항목번호"] in (3, 4, 5):
        print("PL", r["항목번호"], r["항목명"], r["값"], r.get("값_당분기"))
for r in wf:
    if r["원수사명"] == "롯데손해보험" and r["공시분기"] == "2023.1Q" and r["항목번호"] in (1, 5, 6):
        print("WF", r["항목번호"], r["항목명"], r["값"], r.get("값_당분기"))
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
print("gold overlay keys for 롯데 2023.1Q item4:",
      [k for k in (gold.get("set") if isinstance(gold.get("set"), list) else [])
       if isinstance(k, dict) and k.get("원보험사코드") == "KR0003" and k.get("공시분기") == "2023.1Q"][:6])
