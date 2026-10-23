# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("kr0003_verify.py")
s = p.read_text(encoding="utf-8")
a = '("총포괄손익", "분기총포괄손익", "반기총포괄손익")'
b = '("총포괄손익", "분기총포괄손익", "반기총포괄손익", "당기총포괄손익")'
assert s.count(a) == 1
s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
