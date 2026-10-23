s = open("n00_lib.py", encoding="utf-8").read()
s = s.replace('RA_BAD = re.compile(r"처음|최초|신계약|손실|추정|기초|기말|잔액|금융")', 'RA_BAD = re.compile(r"처음|최초|신계약|손실|추정|기초|기말|잔액|보험금융|재보험금융")')
open("n00_lib.py", "w", encoding="utf-8").write(s)
