import re,sys
sys.stdout.reconfigure(encoding="utf-8")
p="data/dart/FY2025_Q2/raw/KR0068_한화생명/xml/20250813001075.xml"
lines=open(p,encoding="utf-8",errors="replace").read().split("\n")
def col(ctx):
    if "NotRelatedToContractsThatExisted" in ctx: return "그밖"
    if "FairValueApproachHasBeen" in ctx: return "공정가치"
    if "ModifiedRetrospectiveApproachHasBeen" in ctx: return "수정소급"
    return None
i=0
while i<len(lines):
    L=lines[i]
    m=re.search(r'ACODE="([^"]*)" ACONTEXT="([^"]*)"',L)
    if m and col(m.group(2)) and ("Finance" in m.group(1) or m.group(1).endswith("ContractualServiceMargin")):
        val=re.sub(r"<[^>]+>","",lines[i+1]).strip()
        ctx=m.group(2)
        sc="별도" if "SeparateMember" in ctx else "연결"
        side="출재" if "ReinsuranceContractsHeld" in ctx else "수재"
        print(i+1,sc,side,ctx.split("_")[0],m.group(1).replace("ifrs-full_","")[:40],col(ctx),val)
    i+=1
