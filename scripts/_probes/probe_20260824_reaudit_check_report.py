# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"C:\Users\sangwook.cho\Desktop\insurequant\artifacts\validation\reaudit_20260824_KR0075_KR0087_KR0073.md"
b = open(p, "rb").read()
print("bytes:", len(b), "BOM:", b[:3] == b"\xef\xbb\xbf")
t = b.decode("utf-8")
print("japanese chars:", len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff]", t)))
print("lines:", len(t.splitlines()))
print("---- first 40 lines ----")
print("\n".join(t.splitlines()[:40]))
