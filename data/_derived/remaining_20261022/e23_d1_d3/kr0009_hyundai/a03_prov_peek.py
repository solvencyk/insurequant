# -*- coding: utf-8 -*-
"""read-only: provenance sidecar blocks of KR0009 (PL + CSM) for the FY2023 quarters + 2024.1Q"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
pv = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
print("PL prov top keys:", [k for k in pv.keys() if k != "cells"])
for c in pv["cells"]:
    if c["company_code"] == "KR0009" and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"):
        print(json.dumps(c, ensure_ascii=False))
cv = json.loads((ROOT / "CSM_waterfall_provenance.json").read_text(encoding="utf-8"))
print("\nCSM prov top keys:", [k for k in cv.keys() if k != "cells"])
for c in cv["cells"]:
    if c["company_code"] == "KR0009" and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"):
        print(json.dumps(c, ensure_ascii=False))
