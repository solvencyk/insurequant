# -*- coding: utf-8 -*-
"""KR0072 step 0 (read-only): full gold entries (PL set, CSM set), dangi pins, ledger pins touching KR0072, plus the live master rows of KR0072 FY2023-FY2024."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
CODE = "KR0072"
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
cgold = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
pins = json.loads((ROOT / "data/_gold/gold_overlay_ledger.json").read_text(encoding="utf-8"))
print("== PL gold set entries of KR0072 (all quarters)")
for e in gold["set"]:
    if e["원보험사코드"] == CODE:
        print(json.dumps(e, ensure_ascii=False))
print("== CSM gold set entries of KR0072 (all quarters)")
for e in cgold["set"]:
    if e["원보험사코드"] == CODE:
        print(json.dumps(e, ensure_ascii=False))
print("== null_dangi KR0072:", [x for x in gold["null_dangi"]["cells"] if x[0] == CODE])
print("== set_dangi KR0072:", [x for x in gold["set_dangi"]["cells"] if x[0] == CODE])
print("== top-level keys of PL gold:", list(gold.keys()), "| null_dangi keys:", [k for k in gold["null_dangi"].keys()], "| set_dangi keys:", [k for k in gold["set_dangi"].keys()])
print("== top-level keys of CSM gold:", list(cgold.keys()))
print("== ledger entries touching KR0072")
for k, v in pins.get("entries", {}).items():
    if f"|{CODE}|" in k:
        print(k, "->", json.dumps(v, ensure_ascii=False))
print("ledger top-level keys:", list(pins.keys()))
