import io,re
p="data/_derived/remaining_20261022/v_oci/locate.py"
s=io.open(p,encoding="utf-8").read()
s=s.replace('''while j>0 and rs[j][2] and rs[j][2][0][0].replace(" ","")!="당기순이익" and i-j<14: j-=1
        if not(rs[j][2] and rs[j][2][0][0].replace(" ","")=="당기순이익"): continue''','''while j>0 and not isni(rs[j][2]) and i-j<14: j-=1
        if not isni(rs[j][2]): continue''')
s=s.replace("def blocks(path):",'''def isni(cells):
    if not cells: return False
    l=cells[0][0].replace(" ","")
    return bool(re.match(r"^(\(.\))?(\d\.)?(당기|반기|분기|당반기|당분기|당\(분\)기|당\(반\)기)?순이익|^(당기|반기|분기)순손익|^당기순이익",l)) and "법인세" not in l and "기타" not in l
def blocks(path):''')
io.open(p,"w",encoding="utf-8").write(s)
