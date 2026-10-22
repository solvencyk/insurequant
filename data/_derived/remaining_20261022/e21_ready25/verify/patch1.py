import re
p="v06_pl_cites.py"
s=open(p,encoding="utf-8").read()
s=s.replace('''    for m in CITE.finditer(cite):
        label, ln, txt = m.group(1).strip(), int(m.group(2)), m.group(3).strip()''','''    parts = []
    for seg in cite.split(" ; "):
        mm = re.match(r"^(.*?)\|L(\d+)\|(.*)$", seg.strip())
        if mm:
            tx = mm.group(3).strip()
            tx = re.split(r"\s+(?=[\(\[]?item|=>|\+)", tx)[0].strip()
            parts.append((mm.group(1).strip(), int(mm.group(2)), tx))
    for label, ln, txt in parts:''')
open(p,"w",encoding="utf-8").write(s)
