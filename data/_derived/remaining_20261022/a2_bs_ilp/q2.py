import json,sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
p=json.load(open(R+"insurance_liability_portfolio_provenance.json",encoding="utf-8"))
print(list(p.keys()))
for k,v in p.items():
    if isinstance(v,list): print(k,len(v))
for c in p["cells"]:
    if c["company_code"]=="KR0073" and c["quarter"]=="2023.4Q":
        print(json.dumps(c,ensure_ascii=False,indent=1)[:4000])
print([b for b in p.get("backfills",[])][-2:])
