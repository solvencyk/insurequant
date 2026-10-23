# -*- coding: utf-8 -*-
"""e23 probe (read-only): Lotte 2023.4Q LOB reader (e21 lotte_combined_read on the annual filing) and the life IS lines of KB라이프 / ABL / KDB vs the e20 candidates."""
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
import e23_read as X  # noqa: E402
import e21_life as L  # noqa: E402
import e21_read as R  # noqa: E402
import e21_t2 as T  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
MEAS = ROOT / "data/_derived/remaining_20261022/e20_held_and_remaining/measure"
cands = {}
for s in ("N2_KBlife_B", "N7_Lotte_FY2023Q4", "N4_ABL_FY2023", "N5_KDB_FY2023", "N6c_HD_FY2023_IRlegs"):
    d = json.loads((MEAS / f"cands_{s}.json").read_text(encoding="utf-8"))
    for c in d["pl_cells"]:
        cands[(c["code"], c["q"], c["item"])] = c
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in pl}
L.SPEC["KR0072"] = [("rev", "보험수익", 1, 1, False), ("cost", "보험비용", 1, -1, True), ("rerev", "재보험수익", 1, 1, False), ("recost", "재보험비용", 1, -1, True)]

print("=== Lotte 2023.4Q lotte_combined_read")
r = T.lotte_combined_read("KR0003", "2023.4Q")
for i in sorted(k for k in r if isinstance(k, int)):
    v = r[i]
    cd = cands.get(("KR0003", "2023.4Q", i))
    print(f"  i{i:>2} old={M.get(('KR0003', i, '2023.4Q'))} read={round(v['val'], 6)} cand={None if cd is None else cd['new']}  {v['formula']} | {v['src']}")
    for p in v["parts"]:
        print(f"        part L{p['line']} {p['printed']} sign {p['sign']} abs {p['abs']} col {p.get('col')} {p['label'][:60]}")

for code, qs in (("KR0099", ["2023.1Q", "2023.2Q", "2023.3Q"]), ("KR0070", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]), ("KR0072", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"])):
    for q in qs:
        fy = T.M.later_fy(q)
        st = R.Stmt(code, fy)
        lr = L.life_is_items(code, fy, "prior", "cum", st=st)
        out = []
        for i in (2, 3, 8):
            cd = cands.get((code, q, i))
            out.append(f"i{i}: old={M.get((code, i, q))} read={round(lr[i]['val'], 6)} cand={None if cd is None else cd['new']}")
        print(code, q, " | ".join(out))
