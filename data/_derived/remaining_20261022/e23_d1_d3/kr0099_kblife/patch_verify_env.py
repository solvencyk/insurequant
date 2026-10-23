# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("kr0099_verify.py")
s = p.read_text(encoding="utf-8")
a = 'PLAN = json.loads((HERE / "e23_plan_kblife.json").read_text(encoding="utf-8"))'
b = 'import os\nPLAN = json.loads((HERE / os.environ.get("KR0099_PLAN", "e23_plan_kblife.json")).read_text(encoding="utf-8"))\nOUTTAG = os.environ.get("KR0099_OUTTAG", "")'
assert s.count(a) == 1
s = s.replace(a, b)
a2 = '(HERE / "kr0099_verify.txt")'
assert s.count(a2) == 1
s = s.replace(a2, '(HERE / f"kr0099_verify{OUTTAG}.txt")')
a3 = '(HERE / "kr0099_verify.json")'
assert s.count(a3) == 1
s = s.replace(a3, '(HERE / f"kr0099_verify{OUTTAG}.json")')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
