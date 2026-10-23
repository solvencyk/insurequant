# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
d = open(sys.argv[1], "rb").read()
for enc in ("utf-8", "cp949"):
    try:
        t = d.decode(enc)
        break
    except UnicodeDecodeError:
        t = d.decode("utf-8", "replace")
i = t.find(sys.argv[2])
print(t[max(0, i - 100): i + int(sys.argv[3])])
