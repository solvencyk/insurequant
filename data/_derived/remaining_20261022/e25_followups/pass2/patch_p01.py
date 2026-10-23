# -*- coding: utf-8 -*-
import io
p = "p01_build_plan.py"
s = io.open(p, encoding="utf-8").read()
old = """    for itm in (5, 6, 9, 10, 11):
        old = lv("KR0068", itm, q)
        if old is not None and abs(old - it[str(itm)]) < 5e-4:
            continue
        if itm not in (5, 6) and "recsm" not in rows:
            continue
"""
new = """    for itm in (5, 6, 9, 10, 11):
        if str(itm) not in it:
            continue
        old = lv("KR0068", itm, q)
        if old is not None and abs(old - it[str(itm)]) < 5e-4:
            continue
"""
assert s.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))
print("patched")
