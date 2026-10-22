import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(ROOT + "CSM_waterfall_provenance.json", encoding="utf-8").read())
print([k for k in d if k != "cells"])
print(len(d["cells"]))
for c in d["cells"]:
    if c["company_code"] in ("KR0003", "KR0079", "KR0001", "KR0068") and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q", "2024.1Q", "2024.2Q", "2024.3Q"):
        print(json.dumps(c, ensure_ascii=False)[:420])
