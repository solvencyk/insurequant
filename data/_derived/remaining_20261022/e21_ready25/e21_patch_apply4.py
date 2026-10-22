"""one-off patcher #4 for e21_apply.py: single-quarter TAX22 groups are tuple literals"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
s = open(H + "e21_apply.py", encoding="utf-8").read()
old = '''    pieces = ["(\\"%s\\", q) for q in (%s)" % (co, ", ".join('"%s"' % q for q in sorted(qs))) for co, qs in sorted(by.items())]'''
new = '''    pieces = [("(\\"%s\\", \\"%s\\")" % (co, qs[0])) if len(qs) == 1 else ("(\\"%s\\", q) for q in (%s)" % (co, ", ".join('"%s"' % q for q in sorted(qs)))) for co, qs in sorted(by.items())]'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(H + "e21_apply.py", "w", encoding="utf-8", newline="\n").write(s)
print("patched apply4")
