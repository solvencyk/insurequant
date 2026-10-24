# -*- coding: utf-8 -*-
"""READ-ONLY pass4 s02: do gold `set` entries with 값 == null exist already (GOLD_SUPPRESSES precedent)? and the null_dangi / set_dangi doc strings for the cells of this ticket."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
gold = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
nn = [e for e in gold["set"] if e["값"] is None]
print("gold set entries with 값 == null:", len(nn))
for e in nn[:20]:
    print("  ", e["원보험사코드"], e["공시분기"], e["항목번호"], "was", e.get("was"), "note:", str(e.get("note"))[:200])
print("--- null_dangi doc keys")
for k, v in gold["null_dangi"].items():
    if k.startswith("_doc"):
        print(k, "->", str(v)[:1800])
        print()
print("--- set_dangi keys:", list(gold["set_dangi"].keys()))
print("--- top-level _doc:", str(gold["_doc"])[:1500])
