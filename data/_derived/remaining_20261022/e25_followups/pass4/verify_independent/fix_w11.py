p="C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent/w11_dy_verify.py"
s=open(p,encoding="utf-8").read()
s=s.replace('''        if re.search(pat,j): return r
''','''        if re.search(pat,j) and last_num(r) is not None: return r
''')
s=s.replace("def find_row(t,pat):","def last_num(r):\n    for c in reversed(r['cells']):\n        v=to_num(c)\n        if v is not None: return v\ndef find_row(t,pat):",1)
open(p,"w",encoding="utf-8").write(s)
