import re, sys, json, io
# independent XML statement-row reader: returns rows [(lineno,label,acode,{ctx:value_mn})]
TE=re.compile(r'<TE\b([^>]*)>(.*?)</TE>',re.S)
def num(s):
    s=re.sub(r'<[^>]+>','',s).strip().replace(',','')
    neg=s.startswith('(') and s.endswith(')')
    s=s.strip('()')
    if not re.fullmatch(r'-?\d+(\.\d+)?',s): return None
    v=float(s)
    return -v if neg else v
def rows(path):
    txt=io.open(path,encoding="utf-8",errors="replace").read()
    # split by TR with line numbers
    out=[]
    for m in re.finditer(r'<TR\b.*?</TR>',txt,re.S):
        ln=txt.count("\n",0,m.start())+1
        blk=m.group(0)
        label=None; code=None; vals={}
        for t in TE.finditer(blk):
            attrs,body=t.group(1),t.group(2)
            a=re.search(r'ACODE="([^"]*)"',attrs)
            if a:
                cm=re.search(r"ACONTEXT=\"([^\"]*)\"",attrs); c=cm.group(1) if cm else "NOCTX"
                code=a.group(1)
                v=num(body)
                if v is not None:
                    vals[c]=v
            elif label is None:
                label=re.sub(r'<[^>]+>','',body).strip()
        out.append((ln,label,code,vals))
    return out
if __name__=="__main__":
    p=sys.argv[1]
    for ln,l,c,v in rows(p):
        if c=="ifrs-full_OtherComprehensiveIncome" and any("Separate" in k for k in v):
            print("OCI row at",ln,l,{k.split("_")[0]:x for k,x in v.items() if "SeparateMember" in k})
