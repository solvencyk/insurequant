# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
t = open(sys.argv[1], "rb").read().decode("cp949", errors="replace")
i = t.find("assert not")
print(t[i:i + 2500])
