import re,sys,csv,collections
sys.stdout.reconfigure(encoding="utf-8")
files={
"2024.4Q":"data/dart/FY2024_Q4/raw/KR0068_한화생명_20250312000939/20250312000939.xml",
"2025.1Q":"data/dart/FY2025_Q1/raw/KR0068_한화생명/20250514001238.xml",
"2025.2Q":"data/dart/FY2025_Q2/raw/KR0068_한화생명/xml/20250813001075.xml",
"2025.3Q":"data/dart/FY2025_Q3/raw/KR0068_한화생명/xml/20251113000814.xml",
"2025.4Q":"data/dart/FY2025_Q4/raw/KR0068_한화생명_20260316001304/20260316001304.xml",
"2026.1Q":"data/dart/FY2026_Q1/raw/KR0068_한화생명/xml/20260529001672.xml",
"2026.2Q":"data/dart/FY2026_Q2/raw/KR0068_한화생명/20260813001536.xml",
}
def col(ctx):
    if "NotRelatedToContractsThatExisted" in ctx: return "그밖"
    if "FullyRetrospective" in ctx: return "완전소급"
    if "FairValueApproachHasBeen" in ctx: return "공정가치"
    if "ModifiedRetrospectiveApproachHasBeen" in ctx: return "수정소급"
    return None
def num(s):
    s=s.strip().replace(",","")
    neg=s.startswith("(")
    s=s.strip("()")
    try: v=float(s)
    except: return None
    return -v if neg else v
out=[]
for q,p in files.items():
    lines=open(p,encoding="utf-8",errors="replace").read().split("\n")
    rl=None
    for i,L in enumerate(lines):
        m=re.match(r"<TE ENG=\"[^\"]*\"[^>]*>([^<]*)</TE>",L)
        if m and "ACODE" not in L: rl=m.group(1).strip(); continue
        m=re.search(r'ACODE="([^"]*)" ACONTEXT="([^"]*)".*?>([^<]*)</TE>',L)
        if not m: continue
        code,ctx,val=m.groups()
        c=col(ctx)
        if not c: continue
        per=ctx.split("_")[0]
        scope="별도" if "SeparateMember" in ctx else ("연결" if "ConsolidatedMember" in ctx else "?")
        side="출재" if "ReinsuranceContractsHeld" in ctx else ("수재" if "InsuranceContractsIssued" in ctx else "?")
        out.append((q,i+1,scope,side,per,code.replace("ifrs-full_",""),c,val,rl))
w=csv.writer(open(sys.argv[1],"w",encoding="utf-8-sig",newline=""))
w.writerow(["filing","line","scope","side","period_ctx","acode","col","raw","rowlabel"])
for r in out: w.writerow(r)
print(len(out))
