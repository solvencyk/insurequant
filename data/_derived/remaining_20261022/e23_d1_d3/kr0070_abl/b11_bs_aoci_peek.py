# -*- coding: utf-8 -*-
"""read-only: IFRS17_BS.json AOCI-related rows of KR0070 (the OCI_VS_BS_AOCI YELLOW pair) next to the PL OCI single quarters of the loaded master"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
rows = [r for r in bs if r.get("원보험사코드") == "KR0070"]
print(len(rows), "BS rows of KR0070; keys", sorted(rows[0].keys()))
items = sorted({(r["항목번호"], r.get("항목명")) for r in rows})
print(items)
for r in sorted(rows, key=lambda r: (r["항목번호"], r["공시분기"])):
    if r["항목번호"] == 4 and r["공시분기"] in ("2022.4Q", "2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"):
        print(r["공시분기"], r["항목번호"], r.get("항목명"), r.get("값"))
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"):
    r = pl[("KR0070", 25, q)]
    print("PL OCI", q, r["값"], r["값_당분기"])
