# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("kr0003_verify.py")
s = p.read_text(encoding="utf-8")
a = '    exp, _c2, _r2 = st.cell("보험영업비용", col)\n'
b = '''    try:
        exp, _c2, _r2 = st.cell("보험영업비용", col)
    except RuntimeError:
        exp, _c2, _r2 = st.cell("보험서비스비용", col)          # the original FY2023 report names the expense block 보험서비스비용
'''
assert s.count(a) == 1
s = s.replace(a, b)
a2 = 'lob23 = lob_items("F" and F["A23"], "당")'
b2 = 'lob23 = lob_items(F["A23"], "당")'
assert s.count(a2) == 1
s = s.replace(a2, b2)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
