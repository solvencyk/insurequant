# -*- coding: utf-8 -*-
"""Read-only: KR0074 mentions in gold overlays and PL master (item 4 = CSM amort) for the three target quarters."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")

g = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
print("user_csm_cells keys", list(g.keys()))


def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if "KR0074" in str(k):
                print("KEY", path + "/" + str(k), json.dumps(v, ensure_ascii=False)[:600])
            walk(v, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if isinstance(v, dict) and (v.get("kr") == "KR0074" or v.get("code") == "KR0074" or v.get("원보험사코드") == "KR0074"):
                print("ITEM", path, i, json.dumps(v, ensure_ascii=False)[:600])
            walk(v, path + f"[{i}]")


walk(g)

pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
print("PL rows", len(pl), "keys", list(pl[0].keys()))
for r in sorted([r for r in pl if r["원보험사코드"] == "KR0074" and r["공시분기"] in ("2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q") and r["항목번호"] in (4, 5, 6, 7)],
                key=lambda r: (r["공시분기"], r["항목번호"])):
    print(r["공시분기"], r["항목번호"], r["항목명"], r["값"], r.get("값_당분기"))
