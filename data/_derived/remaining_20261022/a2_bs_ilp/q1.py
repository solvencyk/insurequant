import json,sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
ilp=json.load(open(R+"insurance_liability_portfolio.json",encoding="utf-8"))
print(type(ilp), len(ilp))
rows=[r for r in ilp if r["원보험사코드"]=="KR0073" and r["공시분기"] in("2023.4Q","2024.1Q","2024.4Q")]
for r in sorted(rows,key=lambda r:(r["공시분기"],r["항목번호"])): print(r)
bs=json.load(open(R+"IFRS17_BS.json",encoding="utf-8"))
print(type(bs),len(bs))
rows=[r for r in bs if r.get("원보험사코드")=="KR0073" and r["공시분기"] in("2023.4Q","2024.4Q")]
for r in sorted(rows,key=lambda r:(r["공시분기"],r["항목번호"])): print(r)
