# -*- coding: utf-8 -*-
"""CSM header path: the first THEAD row is the unit row, so 보험계약마진(CSM) is any element before the last one, not p[0]"""
from pathlib import Path

p = Path("kr0003_verify.py")
s = p.read_text(encoding="utf-8")
a = 'col = next((i for i, p in enumerate(paths) if len(p) >= 2 and "보험계약마진" in nspace(p[0]) and nspace(p[-1]) == "소계"), None)'
b = 'col = next((i for i, p in enumerate(paths) if len(p) >= 2 and any("보험계약마진" in nspace(x) for x in p[:-1]) and nspace(p[-1]) == "소계"), None)'
assert s.count(a) == 1
s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
