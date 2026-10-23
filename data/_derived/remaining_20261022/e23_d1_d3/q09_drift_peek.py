# -*- coding: utf-8 -*-
"""e23 probe (read-only): which cells of the five D1-D3 companies were in the e21 pre-existing drift snapshot (fresh build_pl() with the live gold != live master)?"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
EV = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
d = json.loads((EV / "drift_before.json").read_text(encoding="utf-8"))
print("snapshot", d["made_at"], "PL drift cells", len(d["drift_all"]), "CSM drift", len(d["csm_drift_all"]))
print("by_company:", d["by_company"])
for code in ("KR0099", "KR0003", "KR0070", "KR0072", "KR0009"):
    cells = sorted([tuple(x) for x in d["drift_all"] if x[0] == code], key=lambda x: (x[2], x[1]))
    print(code, len(cells), [f"{q}:{i}" for (_c, i, q) in cells])
print("CSM drift:", [tuple(x) for x in d["csm_drift_all"]][:20])
