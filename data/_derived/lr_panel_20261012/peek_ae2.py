import json, collections
from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
rows = json.load(open(R/"data/loss_ratio/claims_ae_ratio.json", encoding="utf-8"))
c = collections.Counter((r["원보험사코드"], r["공시분기"], r["기준연도"], r.get("사업구분")) for r in rows)
print("dup keys:", [k for k,v in c.items() if v>1])
print(collections.Counter((r["공시분기"], r["기준연도"]) for r in rows))
for r in rows:
    if "사업구분" in r or "dash" in r or r["예상손해율"] is None or r["실제손해율"] is None or r["예실차비율"] is None:
        print({k: r[k] for k in r if k not in ("출처","원문","identity")})
print(collections.Counter(type(r["예상손해율"]).__name__ for r in rows))
for code in ("KR1000","KR0002"):
    for r in rows:
        if r["원보험사코드"]==code: print(code, r["공시분기"], r["기준연도"], r["예상손해율"], r["실제손해율"], r["예실차비율"], r.get("사업구분"), r["플래그"])
