import json,sys
sys.stdout.reconfigure(encoding='utf-8')
R='C:/Users/sangwook.cho/Desktop/insurequant/'
def sk(o,d=0,maxd=3,name=''):
    pad='  '*d
    if isinstance(o,dict):
        print(pad+name+'{dict %d}'%len(o), list(o)[:6])
        if d<maxd:
            for k in list(o)[:4]: sk(o[k],d+1,maxd,str(k)+': ')
    elif isinstance(o,list):
        print(pad+name+'[list %d]'%len(o), json.dumps(o[0],ensure_ascii=False)[:200] if o else '')
    else: print(pad+name+repr(o)[:80])
for f in ['data/compare/panel_compare.json','data/csm_combo/panel_csm_combo.json']:
    print('=====',f); sk(json.load(open(R+f,encoding='utf-8')),0,4)
