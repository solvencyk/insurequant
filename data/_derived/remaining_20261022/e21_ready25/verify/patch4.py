p="v10_note_engine.py"
s=open(p,encoding="utf-8").read()
s=s.replace('''        txts = [c["t"] for c in r["cells"]]
        if "누적" in txts and "3개월" in txts:''','''        txts = [c["t"].replace(" ", "") for c in r["cells"]]
        if "누적" in txts and "3개월" in txts:''')
s=s.replace('''            if c["t"] == "누적":''','''            if c["t"].replace(" ", "") == "누적":''')
open(p,"w",encoding="utf-8").write(s)
