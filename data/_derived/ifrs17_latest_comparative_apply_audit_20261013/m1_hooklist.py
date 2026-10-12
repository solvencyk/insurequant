import re, os
src = open("C:/Users/sangwook.cho/Desktop/insurequant/scripts/prepush_check.py", encoding="utf-8").read()
i = src.index('    fast = ["tests/test_kics_rules_golden.py"')
j = src.index('"tests/unit/"]', i) + len('"tests/unit/"]')
block = src[i:j]
paths = re.findall(r'"(tests/[^"]+)"', block)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "m1_hooklist.txt"), "w", encoding="utf-8").write("\n".join(paths) + "\n")
print(len(paths))
