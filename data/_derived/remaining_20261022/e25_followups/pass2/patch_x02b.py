# -*- coding: utf-8 -*-
import io
src = io.open("patch_x02.py", encoding="utf-8").read()
a = src.index("add = '''") + len("add = '''")
b = src.index("'''\nmarker")
add = src[a:b]
p = "make_x02.py"
s = io.open(p, encoding="utf-8").read()
i = s.index("DST.write_text(")
assert s.count("DST.write_text(") == 1
s = s[:i] + add + s[i:]
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched make_x02 (index based)")
