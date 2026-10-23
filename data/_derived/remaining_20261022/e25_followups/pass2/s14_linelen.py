# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
data = open("C:/Users/sangwook.cho/Desktop/insurequant/TODO_parser_ifrs17.md", "rb").read()
for i, ln in enumerate(data.split(b"\n"), 1):
    if len(ln) > 1000:
        print(i, len(ln), ln[:40].decode("utf-8", "replace"))
