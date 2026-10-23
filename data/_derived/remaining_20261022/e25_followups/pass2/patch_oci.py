# -*- coding: utf-8 -*-
import io
p = "oci_read.py"
s = io.open(p, encoding="utf-8").read()
old = 'if "총포괄손익" not in blob or "기타포괄손익" not in blob or "당기순이익" not in blob:'
new = 'if "총포괄손익" not in blob or "기타포괄손익" not in blob or not any(k in blob for k in ("당기순이익", "반기순이익", "분기순이익")):'
assert s.count(old) == 1
s = s.replace(old, new)
old = 'r24 = [r for r, L in zip(rows, labs) if re.search(r"당기순이익", L) and "조정" not in L and "귀속" not in L][0]'
new = 'r24 = [r for r, L in zip(rows, labs) if re.search(r"(당기|반기|분기)순이익", L) and "조정" not in L and "귀속" not in L and "주당" not in L][0]'
assert s.count(old) == 1
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
