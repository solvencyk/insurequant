p = "e21_t2.py"
s = open(p, encoding="utf-8").read()
a = '''    hdr = " ".join(c["text"] for r in t["rows"][:6] for c in r["cells"])
    cum = "3개월" in hdr and "누적" in hdr
    return dict(cum=cum, step=2 if cum else 1)'''
b = '''    hdr = nl(" ".join(c["text"] for r in t["rows"][:6] for c in r["cells"]))
    cum = "3개월" in hdr and "누적" in hdr
    return dict(cum=cum, step=2 if cum else 1)'''
assert a in s
s = s.replace(a, b, 1)
a2 = '''    hdr = " ".join(c["text"] for r in t["rows"][:4] for c in r["cells"])
    cum = "3개월" in hdr and "누적" in hdr
    unit, uline = unit_above(lines, t["start"])
    div = UNIT_DIV[unit or "백만원"]'''
b2 = '''    hdr = nl(" ".join(c["text"] for r in t["rows"][:4] for c in r["cells"]))
    cum = "3개월" in hdr and "누적" in hdr
    unit = find_unit(lines, t)
    div = UNIT_DIV[unit]'''
assert a2 in s
s = s.replace(a2, b2, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
