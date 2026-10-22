import csv,sys,collections
sys.stdout.reconfigure(encoding="utf-8")
rows=list(csv.DictReader(open(sys.argv[1],encoding="utf-8-sig")))
def num(s):
    s=s.strip().replace(",","");neg=s.startswith("(");s=s.strip("()")
    try:v=float(s)
    except:return None
    return -v if neg else v
codes={"Finance":"InsuranceFinanceIncomeOrExpenses","NewBiz":"EffectsOfContractsInitiallyRecognised","Amort":"RecognitionOfContractualServiceMarginInProfitOrLoss","Estimate":"ChangesInEstimatesThatAdjust","Open/Close":"ContractualServiceMargin"}
g=collections.defaultdict(dict)
for r in rows:
    key=(r["filing"],r["scope"],r["side"],r["period_ctx"],r["acode"],r["rowlabel"][:12])
    g[key][r["col"]]=(num(r["raw"]),r["line"])
for k,v in sorted(g.items()):
    if "InsuranceFinanceIncomeOrExpenses" not in k[4]: continue
    tot=sum(x[0] for x in v.values() if x[0] is not None)
    fv=v.get("공정가치",(0,))[0]
    print(k[0],k[1],k[2],k[3], {c:(x[0],"L"+x[1]) for c,x in v.items()}, "sum",tot, "FVshare %.1f%%"%(100*fv/tot if tot else 0))
