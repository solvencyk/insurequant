import re,sys
sys.stdout.reconfigure(encoding="utf-8")
path=sys.argv[1]; a=int(sys.argv[2]); b=int(sys.argv[3])
lines=open(path,encoding="utf-8",errors="replace").read().split("\n")
def col(ctx):
    if "NotRelatedToContractsThatExisted" in ctx: return "그밖"
    if "FairValueApproachHasBeen" in ctx: return "공정가치"
    if "ModifiedRetrospectiveApproachHasBeen" in ctx: return "수정소급"
    if "FullyRetrospective" in ctx: return "완전소급"
    return "?"
rowlbl=None
for i in range(a-1,min(b,len(lines))):
    L=lines[i]
    m=re.match(r"<TE ENG=\"[^\"]*\"[^>]*>([^<]*)</TE>",L)
    if m and "ACODE" not in L: rowlbl=m.group(1)[:50]; print(i+1,"ROW",rowlbl); continue
    m=re.search(r'ACONTEXT="([^"]*)".*?>([^<]*)</TE>',L)
    if m:
        ctx=m.group(1)
        per=ctx.split("_")[0]
        sep="연결" if "ConsolidatedMember" in ctx and "SeparateMember" not in ctx else ("별도" if "SeparateMember" in ctx else "?")
        print("  ",i+1,per,sep,col(ctx),m.group(2))
