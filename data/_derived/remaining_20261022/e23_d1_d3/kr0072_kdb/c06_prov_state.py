# -*- coding: utf-8 -*-
"""read-only: provenance blocks of KR0072 (PL) and CSM provenance blocks of KR0072 for FY2023 quarters."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
prov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
cprov = json.loads((ROOT / "CSM_waterfall_provenance.json").read_text(encoding="utf-8"))
print("PL provenance top-level keys:", [k for k in prov.keys() if k != "cells"])
print("n cells", len(prov["cells"]))
for c in prov["cells"]:
    if c["company_code"] == "KR0072" and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.4Q"):
        print(json.dumps(c, ensure_ascii=False)[:1800])
        print()
print("CSM provenance keys:", [k for k in cprov.keys() if k != "cells"])
for c in cprov["cells"]:
    if c["company_code"] == "KR0072" and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
        print(json.dumps(c, ensure_ascii=False)[:1500])
        print()
