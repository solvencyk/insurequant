# -*- coding: utf-8 -*-
import io
p = "r01_hd_read.py"
s = io.open(p, encoding="utf-8").read()
old = 'THREE_M_CAP = {"2": r"^\(2\)전반기$|^\(2\)전반기3개월$", "3": r"^\(2\)전분기$|^\(2\)전분기3개월$"}'
new = 'THREE_M_CAP = {"2": r"^\(4\)전반기3개월$", "3": r"^\(4\)전분기3개월$"}'
assert s.count(old) == 1, s.count(old)
io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))
print("ok")
