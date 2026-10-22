# -*- coding: utf-8 -*-
import json
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
rows = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
kr = [r for r in rows if r["원보험사코드"] == "KR0087" and r["공시분기"] in ("2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q")]
L = [str(list(kr[0].keys()))]
for r in sorted(kr, key=lambda r: (r["공시분기"], r["항목번호"])):
    L.append(f"{r['공시분기']} i{r['항목번호']} {r.get('항목명')} 값={r['값']} 당분기={r.get('값_당분기')}")
(ROOT / "data/_derived/remaining_20261022/e19_latest_comparative/KR0087_csm_dump.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
