# -*- coding: utf-8 -*-
import io
p = "oci_read.py"
s = io.open(p, encoding="utf-8").read()
old = 'if "연결" in t["title"] or "요약" in t["title"] or "요약" in (t["caption"] or ""):'
new = 'if "연결" in t["title"] or "요약" in t["title"]:'
assert s.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))
print("patched")
