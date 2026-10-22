import json,sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
p=json.load(open(R+"insurance_liability_portfolio_provenance.json",encoding="utf-8"))
print(json.dumps(p["key"],ensure_ascii=False,indent=1)[:1500])
for c in p["cells"]:
    if (c["company_code"],c["quarter"]) in (("KR0074","2023.4Q"),("KR0073","2024.1Q")):
        print(json.dumps(c,ensure_ascii=False,indent=1)[:5000]); print("=====")
import collections
print(collections.Counter(c.get("basis") for c in p["cells"]))
