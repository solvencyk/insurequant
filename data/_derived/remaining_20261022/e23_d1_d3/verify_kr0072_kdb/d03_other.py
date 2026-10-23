import json, collections
R='C:/Users/sangwook.cho/Desktop/insurequant/'
H=R+'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/head/'
def load(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
# provenance
for n in ['PL_breakdown_provenance','CSM_waterfall_provenance']:
    o=load(H+n+'.json'); w=load(R+n+'.json')
    oc=o['cells'] if isinstance(o,dict) else o; wc=w['cells'] if isinstance(w,dict) else w
    def sel(c): return [json.dumps(x,sort_keys=True,ensure_ascii=False) for x in c if x.get('company_code')=='KR0072']
    a=sel(oc); b=sel(wc)
    print(n,'KR0072 prov cells old',len(a),'new',len(b),'identical',sorted(a)==sorted(b))
    print(' total cells',len(oc),len(wc), 'top-level keys changed:',[k for k in o if k!='cells' and o[k]!=w.get(k)])
# gold
for n in ['user_pl_cells','user_csm_cells']:
    o=load(H+n+'.json'); w=load(R+'data/_gold/'+n+'.json')
    for sect in o:
        if sect==w.get(sect) : pass
    print(n,'sections',list(o.keys()))
    for sect in o:
        ov=o[sect]; wv=w.get(sect)
        if ov==wv: continue
        if isinstance(ov,list):
            def code(e): 
                if isinstance(e,dict): return e.get('원보험사코드') or e.get('code')
                if isinstance(e,list): return e[0]
            a=[x for x in ov if code(x)=='KR0072']; b=[x for x in (wv or []) if code(x)=='KR0072']
            print(' section',sect,'KR0072 old',len(a),'new',len(b),'equal',a==b)
        else:
            print(' section',sect,'changed type',type(ov))
