# -*- coding: utf-8 -*-
"""e23 probe (read-only): FULL notes / why text of the owner-gold cells that the D3 decisions replace."""
import json
import sys
import textwrap
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/../../..")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
cgold = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
PL = [("KR0070", "2023.1Q", 4), ("KR0070", "2023.1Q", 7), ("KR0072", "2023.2Q", 4), ("KR0072", "2023.2Q", 7), ("KR0072", "2023.3Q", 4), ("KR0072", "2023.3Q", 7), ("KR0009", "2023.4Q", 16)]
CS = [("KR0070", "2023.4Q", 1), ("KR0070", "2023.4Q", 4), ("KR0072", "2023.1Q", 4), ("KR0072", "2023.1Q", 5), ("KR0072", "2023.1Q", 6), ("KR0072", "2023.2Q", 4), ("KR0072", "2023.2Q", 5),
      ("KR0072", "2023.4Q", 1), ("KR0072", "2023.4Q", 4), ("KR0009", "2023.3Q", 1), ("KR0009", "2023.3Q", 4), ("KR0009", "2023.4Q", 1), ("KR0009", "2023.4Q", 4)]
for e in gold["set"]:
    if (e["원보험사코드"], e["공시분기"], e["항목번호"]) in PL:
        print("=== PL", e["원보험사코드"], e["공시분기"], e["항목번호"], "값", e["값"], "was", e.get("was"))
        print(textwrap.fill(str(e.get("note")), 200))
for e in cgold["set"]:
    if (e["원보험사코드"], e["공시분기"], e["항목번호"]) in CS:
        print("=== CSM", e["원보험사코드"], e["공시분기"], e["항목번호"], "값", e["값"], "was", e.get("was"))
        print(textwrap.fill(str(e.get("why")), 200))
