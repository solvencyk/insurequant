s = open("n01_notes.py", encoding="utf-8").read()
k = s.index("\nout = {}\nfor (c, q), want")
head, tail = s[:k], s[k:]
open("n00_lib.py", "w", encoding="utf-8").write(head + "\n")
open("n01_notes.py", "w", encoding="utf-8").write("# -*- coding: utf-8 -*-\nfrom n00_lib import *\n" + tail)
