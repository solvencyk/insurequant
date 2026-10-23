# -*- coding: utf-8 -*-
p = "x01_verify_e25.py"
s = open(p, encoding="utf-8").read()
# base root for the "live master / live gold" reads: default = the repo (pre-apply state); after the apply run with E25_BASE=<backup_before_apply> to reproduce the pre-apply verification
s = s.replace('import json\nimport re\nimport sys\n', 'import json\nimport os\nimport re\nimport sys\n', 1)
a = 'ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"\nEV = '
b = 'ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"\nBASE = os.environ.get("E25_BASE") or ROOT      # live master / gold reads (after the apply: E25_BASE=<e25_followups/backup_before_apply>)\nEV = '
assert s.count(a) == 1
s = s.replace(a, b)
n = s.count('open(f"{ROOT}/PL_breakdown.json"') + s.count('open(f"{ROOT}/data/_gold/user_pl_cells.json"')
s = s.replace('open(f"{ROOT}/PL_breakdown.json"', 'open(f"{BASE}/PL_breakdown.json"').replace('open(f"{ROOT}/data/_gold/user_pl_cells.json"', 'open(f"{BASE}/data/_gold/user_pl_cells.json"')
s = s.replace("Usage: x01_verify_e25.py [--mutate KIND]", "Usage: [E25_BASE=<backup root>] x01_verify_e25.py [--mutate KIND]")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("replaced reads:", n)
