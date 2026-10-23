# -*- coding: utf-8 -*-
"""read-only: final state of the 현대해상 gold entries (IR leg, a Tier-1 cell, CSM replace), null_dangi doc key, CSM doc key, and the provenance blocks of 2023.1Q"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
g = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
for e in g["set"]:
    if e["원보험사코드"] == "KR0009" and (e["공시분기"], e["항목번호"]) in {("2023.1Q", 13), ("2023.2Q", 2), ("2023.1Q", 1)}:
        print(json.dumps(e, ensure_ascii=False))
print("\nnull_dangi keys:", [k for k in g["null_dangi"]])
print("null_dangi doc:", g["null_dangi"].get("_doc_e23_kr0009_20261023"))
print("null_dangi KR0009 cells:", [c for c in g["null_dangi"]["cells"] if c[0] == "KR0009"])
c = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
print("\nCSM gold KR0009:")
for e in c["set"]:
    if e["원보험사코드"] == "KR0009":
        print("  ", e["공시분기"], e["항목번호"], e["값"], "was", e["was"], "|", e["why"][:90].replace("\n", " "))
print("\nCSM doc key:", c.get("_doc_e23_kr0009_20261023", "")[:700])
p = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
for b in p["cells"]:
    if b["company_code"] == "KR0009" and b["quarter"] in ("2023.1Q",):
        print("\nPROV", json.dumps(b, ensure_ascii=False)[:1800])
print("\nmerge note:", p["merge_note_20261023_e23_kr0009_hd"][:400])
