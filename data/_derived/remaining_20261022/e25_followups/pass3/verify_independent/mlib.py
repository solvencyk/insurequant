import json, subprocess
R='C:/Users/sangwook.cho/Desktop/insurequant/'
def load(f, head=False):
    if head:
        b=subprocess.run(['git','-C',R,'show','HEAD:'+f],capture_output=True).stdout
        d=json.loads(b.decode('utf-8'))
    else:
        d=json.load(open(R+f,encoding='utf-8'))
    return {(r['원보험사코드'],r['공시분기'],r['항목번호']):r for r in d}
PL=load('PL_breakdown.json'); PL0=load('PL_breakdown.json',True)
def mv(code,q,it,fld='값',old=False):
    r=(PL0 if old else PL).get((code,q,it))
    return None if r is None else r.get(fld)
def nextfy(q):
    y,qq=q.split('.'); return '%d.%s'%(int(y)+1,qq)
def prevq(q):
    y,qq=q.split('.'); n=int(qq[0])
    return ('%s.%dQ'%(y,n-1)) if n>1 else None
