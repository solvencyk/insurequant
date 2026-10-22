import json,sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
s=json.load(open(R+"data/_derived/ilp_restated_comparative.json",encoding="utf-8"))
print([k for k in s if k!="cells"])
for c in s["cells"]:
    if c["company_code"]=="KR0073": print(json.dumps(c,ensure_ascii=False,indent=1)[:3500]); 
txt=open(R+"data/_derived/ilp_restated_comparative.json","rb").read()
print(txt[:60], b"\r\n" in txt, txt[-3:])
t2=json.dumps(s,ensure_ascii=False,indent=1)+"\n"
print("roundtrip", t2.encode("utf-8")==txt)
p=open(R+"insurance_liability_portfolio_provenance.json","rb").read()
print("prov crlf",b"\r\n" in p)
i=open(R+"insurance_liability_portfolio.json","rb").read()
print("ilp crlf",b"\r\n" in i, i[:80])
