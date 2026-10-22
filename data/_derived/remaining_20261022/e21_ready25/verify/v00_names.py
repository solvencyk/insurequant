import json,collections
rows=json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown.json",encoding="utf-8"))
names={}
for r in rows:
    names.setdefault(r["원보험사코드"],{})[r["항목번호"]]=r["항목명"]
for c in ("KR0010","KR0104","KR0068"):
    print(c, json.dumps(names[c],ensure_ascii=False))
rows=json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/CSM_waterfall.json",encoding="utf-8"))
print({r["항목번호"]:r["항목명"] for r in rows})
