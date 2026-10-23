# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("kr0003_diff_vs_backup.py")
s = p.read_text(encoding="utf-8")
a = "sorted((k[1], k[2], hm_ if False else chm[k]['값_당분기'], clm[k]['값_당분기']) for k in cdangi for hm_ in [0])"
b = "sorted((k[1], k[2], chm[k]['값_당분기'], clm[k]['값_당분기']) for k in cdangi)"
assert s.count(a) == 1
s = s.replace(a, b)
a = "    r = subprocess_head = None\n    import subprocess\n"
assert s.count(a) == 1
s = s.replace(a, "")
s = s.replace("import difflib\nimport hashlib\nimport json\nimport sys\n", "import difflib\nimport hashlib\nimport json\nimport subprocess\nimport sys\n")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
