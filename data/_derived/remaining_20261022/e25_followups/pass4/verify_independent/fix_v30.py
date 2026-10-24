# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent/v30_dy_nh_p4.py")
s = p.read_text(encoding="utf-8")
old1 = '''        if c and "재보험계약의 보험서비스결과" in c[0].replace(" ", "") .replace("2.", "2.") or (c and "재보험계약의보험서비스결과" in c[0].replace(" ", "")):'''
new1 = '''        if c and "재보험계약의보험서비스결과" in c[0].replace(" ", ""):'''
assert s.count(old1) == 1
s = s.replace(old1, new1)
old2 = '''for it in (1, 16, 17, 18, 19, 20, 21):
    if it == 19 or q == "2023.2Q":
        pass
'''
assert s.count(old2) == 1
s = s.replace(old2, "")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
