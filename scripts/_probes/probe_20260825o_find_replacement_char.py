# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
t = open("TODO_parser_ifrs17.md", encoding="utf-8").read()
i = t.find("�")
print("index:", i)
print(repr(t[max(0, i - 80): i + 80]))
