# -*- coding: utf-8 -*-
"""e23 step 0 (read-only): full gold entries (set / csm set) + dangi pins + ledger pins of the five D1-D3 companies."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
CODES = {"KR0099", "KR0003", "KR0070", "KR0072", "KR0009"}
QS = {"2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"}
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
cgold = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
pins = json.loads((ROOT / "data/_gold/gold_overlay_ledger.json").read_text(encoding="utf-8"))
print("PL gold set (code in D1-D3 companies, FY2023):")
for e in gold["set"]:
    if e["원보험사코드"] in CODES and e["공시분기"] in QS:
        print("  ", e["원보험사코드"], e["공시분기"], "item", e["항목번호"], "값", e["값"], "was", e.get("was"), "| note:", str(e.get("note"))[:110].replace("\n", " "))
print("CSM gold set:")
for e in cgold["set"]:
    if e["원보험사코드"] in CODES and e["공시분기"] in QS:
        print("  ", e["원보험사코드"], e["공시분기"], "item", e["항목번호"], "값", e["값"], "was", e.get("was"), "| why:", str(e.get("why"))[:110].replace("\n", " "))
print("null_dangi:", [x for x in gold["null_dangi"]["cells"] if x[0] in CODES])
print("set_dangi :", [x[:4] for x in gold["set_dangi"]["cells"] if x[0] in CODES])
print("ledger pin keys with these codes:")
for k, v in pins.get("entries", {}).items():
    if any(f"|{c}|" in k for c in CODES):
        print("  ", k, "->", str(v)[:160])
print("ledger top-level keys:", list(pins.keys()))
