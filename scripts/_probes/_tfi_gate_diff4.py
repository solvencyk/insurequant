# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

before_path = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\artifacts\kics_validation\report_20260831T113807Z.json")
after_path = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\artifacts\kics_validation\report_20260831T113730Z.json")

before = json.loads(before_path.read_text(encoding="utf-8"))
after = json.loads(after_path.read_text(encoding="utf-8"))

def red_set(report):
    out = {}
    for f in report["findings"]:
        if f.get("status") == "RED":
            key = (f.get("원보험사코드"), f.get("공시분기"), f.get("rule"))
            out[key] = f
    return out

b_red = red_set(before)
a_red = red_set(after)

new_red = set(a_red) - set(b_red)
resolved_red = set(b_red) - set(a_red)

print(f"before RED (findings list): {len(b_red)}  after RED (findings list): {len(a_red)}")
print(f"NEW RED: {len(new_red)}")
for k in sorted(new_red, key=lambda x: (str(x[0]), str(x[1]), str(x[2]))):
    f = a_red[k]
    print(f"  {k}")
    print(f"     expected={f.get('expected')!r} actual={f.get('actual')!r} diff={f.get('diff')!r}")
    print(f"     detail={f.get('detail')!r}")
print()
print(f"RESOLVED RED: {len(resolved_red)}")
for k in sorted(resolved_red, key=lambda x: (str(x[0]), str(x[1]), str(x[2]))):
    print(f"  {k}")
