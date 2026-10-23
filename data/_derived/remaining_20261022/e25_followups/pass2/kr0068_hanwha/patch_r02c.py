# -*- coding: utf-8 -*-
import io
p = "r02_hw_read.py"
s = io.open(p, encoding="utf-8").read()
old = 'PR("  items:  " + " ".join(f"{k}={v:,.3f}" for k, v in it.items()) +'
new = 'PR("  items:  " + " ".join(f"{k}={v:,.3f}" for k, v in it.items() if v is not None) +'
assert s.count(old) == 1
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
