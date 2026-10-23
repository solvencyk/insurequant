# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
g = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
print("doc:", str(g.get("_doc"))[:1500])
nulls = [e for e in g["set"] if e.get("값") is None]
print("gold set entries with 값 null:", len(nulls))
for e in nulls[:30]:
    print("  ", e["원보험사코드"], e["항목번호"], e["공시분기"], "was", e.get("was"), "|", (e.get("note") or "")[:150].replace("\n", " "))
print("null_dangi doc:", {k: v for k, v in g["null_dangi"].items() if k != "cells"})
print("set_dangi doc:", {k: v for k, v in g["set_dangi"].items() if k != "cells"})
