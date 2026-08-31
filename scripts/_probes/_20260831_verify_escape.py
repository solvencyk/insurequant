# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
target = "\ub144\ub3c4"  # intended: 년도
print("escaped ->", target, "len:", len(target))
print("hex of chars:", [hex(ord(c)) for c in target])
# also confirm the header cell match
y_short, q_num = "23", "1"
c = "23년도 1/4분기".replace(" ", "")
pattern = f"{y_short}\ub144\ub3c4{q_num}/4\ubd84\uae30"
print("pattern:", pattern)
print("c:", c)
print("match:", pattern in c)
