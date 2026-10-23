# -*- coding: utf-8 -*-
"""read-only: NB_CSM_multiple.json rows of KR0070 (the NB_VS_WATERFALL signals) vs the CSM waterfall item 2 (신계약 CSM) now in the master"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
nb = json.loads((ROOT / "NB_CSM_multiple.json").read_text(encoding="utf-8"))
rows = nb if isinstance(nb, list) else nb.get("rows", nb)
print(type(nb).__name__, len(rows) if hasattr(rows, "__len__") else "")
cs = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))}
for r in rows:
    if isinstance(r, dict) and (r.get("원보험사코드") == "KR0070" or r.get("code") == "KR0070"):
        print(json.dumps(r, ensure_ascii=False)[:400])
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"):
    print(q, "waterfall item 2 (신계약 CSM, 억원) now:", cs[("KR0070", 2, q)]["값"], "single quarter:", cs[("KR0070", 2, q)]["값_당분기"])
