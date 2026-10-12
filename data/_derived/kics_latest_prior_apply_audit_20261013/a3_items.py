import json
d = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/kics_disclosure.json", encoding="utf-8"))
names = {}
for r in d:
    if r["원보험사코드"] == "KR0009" and r["공시분기"] == "2023.1Q":
        names[r["항목번호"]] = (r["항목명"], r.get("값"), r.get("값_적용후"), [k for k in r if k not in ("원보험사코드","원수사명","티커","생손보여부","항목번호","항목명","공시분기","값","값_적용후")])
with open("a3_items.txt", "w", encoding="utf-8") as f:
    for k in sorted(names): f.write(f"{k}\t{names[k]}\n")
