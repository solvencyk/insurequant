# -*- coding: utf-8 -*-
import io
p = "r02_hw_read.py"
s = io.open(p, encoding="utf-8").read()
old = """        rs = [x for x in rr if x["sec"] == sec]
        lead ="""
new = """        rs = [x for x in rr if x["sec"] == sec]
        if not rs:
            continue
        lead ="""
assert s.count(old) == 1
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
