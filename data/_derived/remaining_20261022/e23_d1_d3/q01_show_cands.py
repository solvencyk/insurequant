# -*- coding: utf-8 -*-
"""e23 step 0 (read-only): compact view of the e20 candidate cells of the D1-D3 scenarios (old -> new, gold overlap)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
MEAS = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
SCN = sys.argv[1:] or ["N2_KBlife_B", "N7_Lotte_FY2023Q4", "N4_ABL_FY2023", "N5_KDB_FY2023", "N6c_HD_FY2023_IRlegs"]
for s in SCN:
    d = json.loads((MEAS / f"cands_{s}.json").read_text(encoding="utf-8"))
    print("=" * 30, s, "keys:", list(d.keys()))
    byq = {}
    for c in d["pl_cells"]:
        byq.setdefault((c["code"], c["q"]), []).append(c)
    for (code, q), cs in sorted(byq.items()):
        print(f"-- PL {code} {q}: {len(cs)} cells")
        print("   " + "; ".join(f"i{c['item']}: {c['old']}->{c['new']}" + (f" [GOLD {c['gold']}]" if c.get("gold") is not None else "") for c in cs))
    byq = {}
    for c in d.get("csm_cells", []):
        byq.setdefault((c["code"], c["q"]), []).append(c)
    for (code, q), cs in sorted(byq.items()):
        print(f"-- CSM {code} {q}: {len(cs)} cells")
        print("   " + "; ".join(f"i{c['item']}: {c['old']}->{c['new']}" + (f" [GOLD {c.get('gold')}]" if c.get("gold") is not None else "") for c in cs))
