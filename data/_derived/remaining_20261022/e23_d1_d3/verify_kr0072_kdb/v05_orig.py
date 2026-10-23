# Read the ORIGINAL-vintage filings' cells behind the replaced owner-gold entries (own code), print row + table header + column.
import re, json
ROOT='C:/Users/sangwook.cho/Desktop/insurequant/'
V=ROOT+'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/'
src=open(V+'v01_reread.py',encoding='utf-8').read()
exec(src.split("res=[]")[0].split("with open(K+'e23_plan_kdb_final.json'")[0])
# re-define helpers (they live after the 'with open' line in v01)
exec("def lines(path):\n    if path not in _cache:\n        with open(ROOT+path,encoding='utf-8',errors='replace') as f: _cache[path]=f.read().split(chr(10))\n    return _cache[path]\n_cache={}")
exec(src[src.index('def strip'):src.index('res=[]')])
base={'Q1':'data/dart/FY2023_Q1/raw/KR0072_케이디비생명보험/xml/20230515002450.xml',
      'Q2':'data/dart/FY2023_Q2/raw/KR0072_케이디비생명보험/xml/20230814003052.xml',
      'Q3':'data/dart/FY2023_Q3/raw/KR0072_케이디비생명보험/xml/20231114002983.xml',
      'Q4':'data/dart/FY2023_Q4/raw/KR0072_케이디비생명보험_20240401002710/xml/20240401002710.xml'}
want=[('CSM 2023.1Q i4 gold -833.3','Q1',30809),('CSM 2023.1Q i5 gold -111.25','Q1',30834),('CSM 2023.1Q i6 gold 4727.25','Q1',30950),
      ('CSM 2023.2Q i4 gold -685.55','Q2',35942),('CSM 2023.2Q i5 gold -234.15','Q2',35974),
      ('CSM 2023.4Q i1 gold 5239.4 (orig annual?)','Q4',57765),('CSM 2023.4Q i4 gold -2103.5 (orig annual?)','Q4',57797),
      ('PL 2023.2Q i4 gold 23415','Q2',40301),('PL 2023.3Q i4 gold 35250','Q3',46159)]
out=open(V+'v05_orig.txt','w',encoding='utf-8')
for tag,q,ln in want:
    L=lines(base[q])
    a,b,cells,hit=tr_of(L,ln)
    ta=table_of(L,ln)
    ttl=[]
    k=ta-1
    while k>0 and len(ttl)<3:
        s=strip(L[k])
        if s: ttl.append(s[:80])
        k-=1
    out.write(f'{tag} | file {q} L{ln} hit_col={hit} row={cells}\n   header={[" | ".join(r) for r in header_rows(L,ta)][:2]} prev_text={ttl}\n')
# also: does the original annual (Q4) CSM table show the FY2023 opening 569,595 and closing?
print('done')
