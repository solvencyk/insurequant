import sys,re,collections; sys.stdout.reconfigure(encoding="utf-8")
def parse(p):
    L=open(p,encoding="utf-8",errors="replace").read().splitlines()
    out=collections.Counter(); i=0
    while i<len(L):
        l=L[i]
        m=re.match(r"\s*(RED|YELLOW)\s+\[(.*?)\]\s+(\S+)\s+(.*)$",l)
        if m:
            det=L[i+1].strip() if i+1<len(L) else ""
            out[(m.group(1),m.group(2),m.group(3),m.group(4).strip(),det[:300])]+=1
            i+=2; continue
        i+=1
    return out
b=parse("gates_before/data_contract.txt"); a=parse("gates_after/data_contract.txt")
print("before findings",sum(b.values()),"after",sum(a.values()))
for k in sorted(set(a)-set(b)): print("NEW  ",k)
for k in sorted(set(b)-set(a)): print("GONE ",k)
for k in a:
    if a[k]!=b.get(k,0) and k in b: print("COUNT CHANGE",k,b[k],"->",a[k])
