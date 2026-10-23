# -*- coding: utf-8 -*-
import json
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
for f in ("CSM_waterfall.json", "NB_CSM_multiple.json", "PL_breakdown.json"):
    rows = json.load(open(R + f, encoding="utf-8"))
    for code in ("KR0099", "KR0003", "KR0070", "KR0009"):
        qs = sorted({r["공시분기"] for r in rows if r["원보험사코드"] == code}, key=lambda q: (int(q[:4]), int(q[5])))
        print(f, code, "first", qs[0], "latest", qs[-1], "n", len(qs))
