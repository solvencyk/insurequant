import re
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val/vtab.py"
s = open(p, encoding="utf-8").read()
s = s.replace('        if "<TABLE" in up:\n            if depth == 0:\n                start = i\n                buf = []\n            depth += 1\n',
 '        nopen = len(re.findall(r"<TABLE[\s>]", up))\n        nclose = up.count("</TABLE>")\n        if nopen:\n            if depth == 0:\n                start = i\n                buf = []\n            depth += nopen\n')
s = s.replace('        if "</TABLE>" in up and depth > 0:\n            depth -= 1\n            if depth == 0:',
 '        if nclose and depth > 0:\n            depth -= nclose\n            if depth <= 0:\n                depth = 0')
open(p, "w", encoding="utf-8").write(s)
