# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
g = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
c = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
for e in g["set"][-60:]:
    if (e["항목번호"], e["공시분기"]) in ((4, "2023.1Q"), (15, "2023.1Q"), (30, "2023.2Q"), (7, "2023.3Q"), (17, "2023.1Q"), (22, "2023.3Q")):
        print(json.dumps(e, ensure_ascii=False))
        print()
for e in c["set"][-15:]:
    if (e["항목번호"], e["공시분기"]) in ((5, "2023.2Q"),):
        print(json.dumps(e, ensure_ascii=False))
