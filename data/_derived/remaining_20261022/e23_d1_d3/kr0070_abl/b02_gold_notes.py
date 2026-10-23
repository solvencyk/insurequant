# -*- coding: utf-8 -*-
"""read-only: full notes of the ABL owner-gold entries that the D3 load touches or sits next to."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
cg = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
print("PL gold _doc:", str(gold.get("_doc"))[:1500])
print()
for e in gold["set"]:
    if e["원보험사코드"] == "KR0070" and (e["항목번호"], e["공시분기"]) in [(4, "2023.1Q"), (7, "2023.1Q")]:
        print(json.dumps(e, ensure_ascii=False, indent=1))
print()
for e in cg["set"]:
    if e["원보험사코드"] == "KR0070" and e["공시분기"] == "2023.4Q":
        print(json.dumps(e, ensure_ascii=False, indent=1))
print("CSM gold keys sample:", sorted(cg.keys()))
nd = gold["null_dangi"]
print("null_dangi keys:", sorted(nd.keys()))
print("set_dangi keys:", sorted(gold["set_dangi"].keys()))
print("set_dangi sample:", gold["set_dangi"]["cells"][:2])
