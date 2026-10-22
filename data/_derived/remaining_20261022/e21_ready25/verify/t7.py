import json,sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
m={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
h={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open("head/PL_breakdown.json",encoding="utf-8"))}
for c in ("KR0001","KR0003"):
  for q in ("2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q"):
    print(c,q,[(i,h.get((c,q,i)),m.get((c,q,i))) for i in (4,5,9,10)])
