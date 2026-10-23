import re, glob, html, sys
R='C:/Users/sangwook.cho/Desktop/insurequant/'
def path(q, code):
    fy,qq=q.split('.')   # '2025.2Q'
    import os
    d=glob.glob(R+'data/dart/FY%s_Q%s/raw/%s_*/**/*.xml'%(fy,qq[0],code),recursive=True)
    d=[x for x in d if 'document.zip' not in x]
    return max(d,key=os.path.getsize) if d else None
_tag=re.compile(r'<[^>]+>')
def clean(s):
    s=_tag.sub('',s); s=html.unescape(s).replace('\xa0',' ')
    return re.sub(r'\s+',' ',s).strip()
def tables(p):
    txt=open(p,encoding='utf-8',errors='replace').read()
    # line offsets
    out=[]
    for m in re.finditer(r'<TABLE\b.*?</TABLE>',txt,flags=re.S|re.I):
        ln=txt.count('\n',0,m.start())+1
        rows=[]
        for rm in re.finditer(r'<TR\b.*?</TR>',m.group(0),flags=re.S|re.I):
            cells=[]
            for cm in re.finditer(r'<(TD|TH|TE|TU)\b(.*?)>(.*?)</\1>',rm.group(0),flags=re.S|re.I):
                cs=1
                mm=re.search(r'COLSPAN="?(\d+)',cm.group(2),re.I)
                if mm: cs=int(mm.group(1))
                cells.append(clean(cm.group(3)))
                for _ in range(cs-1): cells.append('')
            lnr=ln+m.group(0).count('\n',0,rm.start())
            rows.append((lnr,cells))
        out.append((ln,rows))
    return out
def num(s):
    s=s.strip().replace(',','')
    if s in ('','-','–'): return None
    neg=False
    if s.startswith('(') and s.endswith(')'): neg=True; s=s[1:-1]
    if s.startswith('△'): neg=True; s=s[1:]
    try: v=float(s)
    except: return None
    return -v if neg else v
def dump(p,pat,ctx=0,maxrows=80,tbl_pat=None):
    T=tables(p)
    for i,(ln,rows) in enumerate(T):
        flat=' '.join(' '.join(c) for _,c in rows)
        if re.search(pat,flat):
            print('=== table#%d line %d rows %d'%(i,ln,len(rows)))
            for lr,c in rows[:maxrows]:
                print(lr,'|'.join(c))
