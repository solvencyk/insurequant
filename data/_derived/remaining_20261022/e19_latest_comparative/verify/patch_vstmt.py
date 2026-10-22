p="vstmt.py"
s=open(p,encoding="utf-8").read()
s=s.replace('''    elif ncol == 2:
        idx = {"cur": 0, "prior": 1}[which]''','''    elif ncol in (2, 3):
        idx = {"cur": 0, "prior": 1}[which]''')
s=s.replace('''    s = NUMB.sub("", s)
    return s.strip()''','''    s = NUMB.sub("", s)
    s = re.sub(r"\s*\(주[\d,\s]*\)\s*$", "", s)
    return s.strip()''')
open(p,"w",encoding="utf-8").write(s)
