p="vstmt.py"
s=open(p,encoding="utf-8").read()
s=s.replace('idx = {"cur": 1, "prior": 3}[which]','idx = {"cur": 1, "prior": 3, "cur3": 0, "prior3": 2}[which]')
open(p,"w",encoding="utf-8").write(s)
