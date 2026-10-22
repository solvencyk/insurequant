import re,sys
sys.stdout.reconfigure(encoding="utf-8")
path=sys.argv[1]; a=int(sys.argv[2]); b=int(sys.argv[3])
lines=open(path,encoding="utf-8",errors="replace").read().split("\n")
row=[];rl=None
for i in range(a-1,min(b,len(lines))):
    L=lines[i]
    if "<TR" in L: row=[];rl=i+1
    for m in re.finditer(r"<(TD|TH|TU)[^>]*>(.*?)</\1>",L):
        t=re.sub(r"<[^>]+>","",m.group(2)).strip()
        row.append(t[:60])
    if "</TR>" in L:
        print(rl,"|".join(row)); row=[]
    if re.search(r"<(TABLE|/TABLE)",L): print(i+1,L.strip()[:80])
