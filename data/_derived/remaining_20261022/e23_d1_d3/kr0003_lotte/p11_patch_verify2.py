# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("kr0003_verify.py")
s = p.read_text(encoding="utf-8")
a = s.index("def all_tables(L):")
b = s.index("def header_paths(L, a, b):")
new = '''def all_tables(L):
    """[(a, b)] 0-based inclusive bounds of every LEAF <TABLE>...</TABLE> (tables that contain another table are skipped: their rows would mix the inner rows in)"""
    out, stack = [], []
    for k, s in enumerate(L):
        if re.match(r"\s*<TABLE\b", s, re.I):
            if stack:
                stack[-1][1] = True                # the enclosing table has a child
            stack.append([k, False])
        elif re.match(r"\s*</TABLE", s, re.I) and stack:
            a, has_child = stack.pop()
            if not has_child:
                out.append((a, k))
    return out


'''
s = s[:a] + new + s[b:]
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
