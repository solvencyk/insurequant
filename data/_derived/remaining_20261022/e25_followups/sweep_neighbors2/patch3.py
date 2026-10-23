p = "c01_csm.py"
s = open(p, encoding="utf-8").read()
a = s.index('    "KR0072": {')
b = s.index('    "KR0099": {')
new72 = '''    "KR0072": {1: lambda x: x.startswith("1.기초보험계약자산및부채"), 2: lambda x: x.startswith("(3)최초인식한계약의효과"), 3: lambda x: x.startswith("6.보험금융손익"),
               4: lambda x: x.startswith("(1)보험계약마진을조정하는추정치의변동분") or x.startswith("(1)보험계약마진을조정하는추"), 5: lambda x: x.startswith("(1)서비스이전을반영하기위"),
               6: lambda x: re.match(r"^(8|9)\.(당기말|전분기말|전반기말|전기말|분기말|반기말|기말)보험계약자산및부채", x) is not None},
'''
s = s[:a] + new72 + s[b:]
s = s.replace('''        cap = E.nl(t["caption"] or "")
        try:''', '''        cap = E.nl(t["caption"] or "")
        if code == "KR0099" and not ("적용하지않은" in cap and "재보험" not in cap):
            continue
        if code == "KR0072" and ("배당" in cap or "(7)" in cap):
            continue
        try:''')
open(p, "w", encoding="utf-8").write(s)
