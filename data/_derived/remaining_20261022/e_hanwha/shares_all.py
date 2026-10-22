import csv,sys,collections
sys.stdout.reconfigure(encoding="utf-8")
rows=list(csv.DictReader(open(sys.argv[1],encoding="utf-8-sig")))
def num(s):
    s=s.strip().replace(",","");neg=s.startswith("(");s=s.strip("()")
    try:v=float(s)
    except:return None
    return -v if neg else v
g=collections.defaultdict(dict)
for r in rows:
    if r["period_ctx"].startswith("P") or r["period_ctx"].startswith("BP"): 
        if not r["acode"].endswith("ContractualServiceMargin"): continue
    key=(r["filing"],r["scope"],r["side"],r["period_ctx"][:4],r["acode"][:60])
    g[key][r["col"]]=num(r["raw"])
for k,v in sorted(g.items()):
    if k[1]!="별도": continue
    tot=sum(x for x in v.values() if x is not None)
    fv=v.get("공정가치") or 0
    print(k[0],k[2],k[3],k[4][:55],v,"sum",tot,"FV%% %.0f"%(100*fv/tot if tot else 0))
