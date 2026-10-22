import json, io
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
out = io.open(R+"data/_derived/remaining_20261022/e19_latest_comparative/KR0005_s2_master.txt","w",encoding="utf-8")
def w(*a): out.write(" ".join(str(x) for x in a)+"\n")
pl = json.load(io.open(R+"PL_breakdown.json",encoding="utf-8"))
kr = [r for r in pl if r.get("원보험사코드")=="KR0005"]
w("KR0005 rows", len(kr))
qs = ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q","2025.1Q"]
items = sorted({r["항목번호"] for r in kr})
w("items", items)
for it in items:
    nm = [r["항목명"] for r in kr if r["항목번호"]==it][0]
    w("item", it, nm)
    for q in qs:
        rr = [r for r in kr if r["항목번호"]==it and r["공시분기"]==q]
        if rr:
            w("   ", q, rr[0].get("값"), rr[0].get("값_당분기"), {k:v for k,v in rr[0].items() if k not in ("원보험사코드","원수사명","티커","생손보여부","항목번호","항목명","공시분기","값","값_당분기")})
        else:
            w("   ", q, "ABSENT")
g = json.load(io.open(R+"data/_gold/user_pl_cells.json",encoding="utf-8"))
w("---- gold KR0005")
for k in ("set",):
    for e in g[k]:
        if e.get("원보험사코드")=="KR0005": w(k, json.dumps(e,ensure_ascii=False))
for k in ("null_dangi","set_dangi"):
    v = g[k]
    w(k, type(v).__name__, list(v.keys()) if isinstance(v,dict) else "")
    cells = v["cells"] if isinstance(v,dict) else v
    for c in cells:
        if "KR0005" in json.dumps(c): w(k, json.dumps(c,ensure_ascii=False))
    w(k, "total", len(cells))
    if isinstance(v,dict):
        w(json.dumps({a:b for a,b in v.items() if a!="cells"},ensure_ascii=False)[:800])
    w(k, "last3", [json.dumps(c,ensure_ascii=False)[:400] for c in cells[-3:]])
out.close()
