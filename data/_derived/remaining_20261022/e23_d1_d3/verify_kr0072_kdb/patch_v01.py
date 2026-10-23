import re
p='C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/v01_reread.py'
s=open(p,encoding='utf-8').read()
old_start=s.index('def tr_of'); old_end=s.index('def table_of')
new='''def tr_of(L,ln):
    i=ln-1
    a=i
    while a>=0 and not L[a].lstrip().startswith('<TR'): a-=1
    b=i
    while b<len(L) and '</TR>' not in L[b]: b+=1
    # cells with line spans
    cells=[];hit=None
    txt='\n'.join(L[a:b+1])
    for m in re.finditer(r'<(TD|TE|TH|TU)\b[^>]*>(.*?)</\1>',txt,re.S):
        l0=a+1+txt.count('\n',0,m.start()); l1=a+1+txt.count('\n',0,m.end())
        cells.append(strip(m.group(2)))
        if l0<=ln<=l1: hit=len(cells)-1
    tr_of.hit=hit
    return a,b,cells
'''
s=s[:old_start]+new+s[old_end:]
s=s.replace("col=[i for i,c in enumerate(cells) if c==printed]","col=[tr_of.hit] if tr_of.hit is not None and cells[tr_of.hit]==printed else []")
s=s.replace("if L[a].lstrip().upper().startswith('<TABLE')","if L[a].lstrip().upper().startswith('<TABLE')")
s=s.replace("while i<len(L) and len(rows)<n:\n        if L[i].lstrip().startswith('<TR'):\n            a,b,c=tr_of(L,i+1); rows.append(c); i=b","while i<len(L) and len(rows)<n:\n        if L[i].lstrip().startswith('<TR'):\n            a,b,c=tr_of(L,i+1); rows.append(c); i=b")
# don't print Korean to console
s=s.replace("for r in bad: print(r['tag'],r['line'],r['printed'],r['label'][:40],r['plan_label'] and r['plan_label'][:40],r['line_has'],r['lab_ok'],r['val_ok'],r['col'])","open(OUT+'v01_flagged.txt','w',encoding='utf-8').write('\n'.join(json.dumps(r,ensure_ascii=False) for r in bad))")
open(p,'w',encoding='utf-8').write(s)
