# -*- coding: utf-8 -*-
import io
p = "r01_dy_read.py"
s = io.open(p, encoding="utf-8").read()
old = 'if "3개월" in hdr and "누적" in hdr and "기초" not in blob and must in'
new = 'if "3개월" in hdr and "누적" in hdr and not any(k in blob for k in ("기말", "잔여보장", "기초보험계약", "기초장부금액")) and must in'
assert s.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))
print("patched")
