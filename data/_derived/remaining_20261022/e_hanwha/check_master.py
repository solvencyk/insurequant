import csv,json,sys,collections
sys.stdout.reconfigure(encoding="utf-8")
rows=list(csv.DictReader(open("data/_derived/remaining_20261022/e_hanwha/csm_method_cells.csv",encoding="utf-8-sig")))
def num(s):
    s=s.strip().replace(",","");neg=s.startswith("(");s=s.strip("()")
    return -float(s) if neg else float(s)
m=json.load(open("CSM_waterfall.json",encoding="utf-8"))
mm={(r["공시분기"],r["항목번호"]):r["값"] for r in m if r["원보험사코드"]=="KR0068"}
agg=collections.defaultdict(float)
for r in rows:
    if r["scope"]!="별도" or r["side"]!="수재": continue
    pc=r["period_ctx"]; a=r["acode"]
    if a=="ContractualServiceMargin":
        kind="open" if pc.startswith("P") and "eFY" in pc or pc.startswith("PFY") and pc.endswith("eFY") else None
        if pc.startswith("CFY"): kind="close"
        elif pc.startswith("PFY") and "e" in pc[-3:]: kind="open"
        else: kind=None
    elif "ChangesInEstimates" in a: kind="est"
    elif "EffectsOfContractsInitially" in a: kind="new"
    elif "InsuranceFinance" in a: kind="int"
    elif "RecognitionOfContractualServiceMargin" in a: kind="amort"
    else: kind=None
    if kind and (pc.startswith("CFY") or kind=="open"):
        agg[(r["filing"],kind)]+=num(r["raw"])
no={"open":1,"new":2,"int":3,"est":4,"amort":5,"close":6}
for q in ["2025.3Q","2025.4Q","2026.1Q","2026.2Q"]:
    v={k:agg[(q,k)]/100 for k in no}
    ident=v["open"]+v["new"]+v["int"]+v["est"]+v["amort"]-v["close"]
    print(q,{k:round(x,1) for k,x in v.items()},"identity resid",round(ident,1))
    print("  master",{k:mm.get((q,n)) for k,n in no.items()})
