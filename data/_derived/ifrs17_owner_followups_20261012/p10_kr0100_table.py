# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
t = json.loads(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/bspl_followup_20261011/kr0100_item20_table.json", "rb").read().decode("utf-8"))
for r in t:
    print(r["quarter"], "master", r["master"], r["master_holds"], "| D1", r["D1"], "SA", r["SA"], "D2", r["D2"], "| K", r["K_IFRS_line"], "| res D1/D2/K", None if r["residual_if_D1"] is None else round(r["residual_if_D1"]), None if r["residual_if_D2"] is None else round(r["residual_if_D2"]), None if r["residual_if_K"] is None else round(r["residual_if_K"]), "|", r["source"])
