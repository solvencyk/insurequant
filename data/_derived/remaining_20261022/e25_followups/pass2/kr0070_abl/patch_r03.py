# -*- coding: utf-8 -*-
import io
p = "r03_abl_read.py"
s = io.open(p, encoding="utf-8").read()
old = """        if sec is None:
            continue
        if lab not in out[sec]:
            out[sec][lab] = n
            order[sec].append(lab)
    return out, order"""
new = """        if sec is None:
            continue
        if lab in ("기타사업비용", "합계"):
            out.setdefault("_tail", {}).setdefault(lab, n)
            continue
        if lab not in out[sec]:
            out[sec][lab] = n
            order[sec].append(lab)
    return out, order"""
assert s.count(old) == 1
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
