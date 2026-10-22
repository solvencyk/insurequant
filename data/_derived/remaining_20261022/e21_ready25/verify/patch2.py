p="xmlrd.py"
s=open(p,encoding="utf-8").read()
s=s.replace('s = re.sub(r"<[^>]+>", "", s)','s = re.sub(r"</?[A-Za-z][^>]*>", "", s)')
open(p,"w",encoding="utf-8").write(s)
