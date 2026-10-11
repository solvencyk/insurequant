# -*- coding: utf-8 -*-
import sys, re
import fitz
sys.stdout.reconfigure(encoding="utf-8")
f, pat = sys.argv[1], sys.argv[2]
doc = fitz.open(f)
for i in range(len(doc)):
    t = doc[i].get_text()
    flat = "".join(t.split())
    if re.search(pat, flat):
        print("== page", i + 1, len(flat))
        # print lines containing the pattern
        for ln in t.splitlines():
            if re.search(pat, "".join(ln.split())):
                print("   ", ln.strip()[:160])
