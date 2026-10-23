# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("kr0099_verify_mutation.py")
s = p.read_text(encoding="utf-8")
s = s.replace('plan = json.loads((HERE / "e23_plan_kblife.json").read_text(encoding="utf-8"))', 'base = json.loads((HERE / "e23_plan_kblife.json").read_text(encoding="utf-8"))\nplan = base')
s = s.replace("    p = copy.deepcopy(plan)\n    # rebind helper closures onto the copy\n    globals()[\"plan\"] = p\n", "    p = copy.deepcopy(base)\n    globals()[\"plan\"] = p\n")
s = s.replace("-2)))", "-1)))") if False else s
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
