p="vstmt.py"
s=open(p,encoding="utf-8").read()
s=s.replace('NUMB = re.compile(r"^(?:\(\d+\)|\d+\.|[가-힣]\.)\s*")','NUMB = re.compile(r"^(?:\(\d+\)|\d+\)|\d+\.|[가-힣]\.)\s*")')
old_start=s.index("        out[26] = pick(")
old_end=s.index("        s = sum(out[k]")
new='''        out[26] = pick(lambda l: "공정가치" in l and ("평가손익" in l or "관련손익" in l) and "지분" not in l and "유가증권" not in l and "기대신용" not in l and "재분류" not in l and "항목" not in l)
        out[27] = pick(lambda l: (not l.startswith("재보험")) and l.startswith("보험") and "금융" in l and ("순" in l))
        out[30] = pick(lambda l: l.startswith("재보험") and "금융" in l and "순" in l)
        out[28] = pick(lambda l: "위험회피" in l)
        out[29] = pick(lambda l: ("지분" in l or "유가증권" in l) and "평가손익" in l)
'''
s=s[:old_start]+new+s[old_end:]
open(p,"w",encoding="utf-8").write(s)
