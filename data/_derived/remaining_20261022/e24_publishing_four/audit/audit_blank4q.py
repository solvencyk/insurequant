import json,sys,subprocess
sys.stdout.reconfigure(encoding='utf-8')
R='C:/Users/sangwook.cho/Desktop/insurequant/'
pre=subprocess.run(['git','-C',R[:-1],'show','d5077c7b:PL_breakdown.json'],capture_output=True).stdout.decode('utf-8')
P=json.loads(pre); N=json.load(open(R+'PL_breakdown.json',encoding='utf-8'))
for c in ('KR0009','KR0003'):
  for it in (1,24):
    for lab,D in (('pre',P),('now',N)):
        print(c,it,lab,[(r['공시분기'],r.get('값'),r.get('값_당분기')) for r in D if r['원보험사코드']==c and r['항목번호']==it and r['공시분기'].startswith('2023') ])
