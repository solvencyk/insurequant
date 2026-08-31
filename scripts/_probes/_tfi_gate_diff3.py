# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

before_path = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\artifacts\kics_validation\report_20260831T113807Z.json")
after_path = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\artifacts\kics_validation\report_20260831T113730Z.json")

before = json.loads(before_path.read_text(encoding="utf-8"))
after = json.loads(after_path.read_text(encoding="utf-8"))

print("sample finding keys:", list(before["findings"][0].keys()))
print()
# find any RED in findings and print its exact dict
for f in before["findings"]:
    if f.get("status") == "RED":
        print("sample RED finding:", f)
        break
