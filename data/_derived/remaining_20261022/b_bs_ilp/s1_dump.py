import json, sys
sys.stdout.reconfigure(encoding="utf-8")
D="data/_derived/remaining_20261022/b_bs_ilp/"
for f,tag in [("IFRS17_BS.json","BS"),("insurance_liability_portfolio.json","ILP")]:
    d=json.load(open(f,encoding="utf-8"))
    kr=[r for r in d if r["원보험사코드"]=="KR0073"]
    qs=sorted({r["공시분기"] for r in kr})
    items={}
    for r in kr: items[r["항목번호"]]=r["항목명"]
    print("==",tag,len(kr),qs)
    print({k:items[k] for k in sorted(items)})
    print("other keys:", sorted({k for r in kr for k in r}))
    # table items x quarters
    tab={(r["항목번호"],r["공시분기"]):r["값"] for r in kr}
    print("item", *qs, sep="\t")
    for i in sorted(items):
        print(i, items[i][:18], *[("" if tab.get((i,q)) is None and (i,q) not in tab else f"{tab[(i,q)]:.0f}" if tab[(i,q)] is not None else "None") for q in qs], sep="\t")
