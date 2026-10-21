import json, sys
sys.stdout.reconfigure(encoding="utf-8")
prov = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown_provenance.json", encoding="utf-8"))
print("top keys:", [k for k in prov if k != "cells"])
for c in prov["cells"]:
    if c["company_code"] == "KR0073" and c["quarter"] in ("2023.1Q", "2023.3Q", "2023.4Q", "2024.2Q", "2024.4Q"):
        print(json.dumps(c, ensure_ascii=False)[:900])
        print()
