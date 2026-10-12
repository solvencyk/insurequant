# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(R + "insurance_liability_portfolio_provenance.json", "rb").read().decode("utf-8"))
for c in d["cells"]:
    if c["company_code"] == "KR0100":
        print(c["quarter"], c["item_block"], c["source_file"].split("/")[-1], "page", c.get("page"), "flags", c.get("flags"), "| prior_year_end", c.get("prior_year_end_column_eok"), "| checks", {k: v for k, v in c["checks"].items() if k in ("bs20_eok", "filing_bs_eok", "ratio_filing_bs", "ratio_bs20", "bs20_master_disagrees")}, "| items", c["items_eok"])
