import json,sys
sys.stdout.reconfigure(encoding="utf-8")
s=json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ilp_restated_comparative.json",encoding="utf-8"))
print(len(s["cells"]))
for c in s["cells"]: print(c["company_code"],c["quarter"],c.get("basis"),c.get("restated_bs_insurance_contract_liability_eok"),c.get("restated_bs_source"), c.get("bs_item20_fy2023_original_eok"))
