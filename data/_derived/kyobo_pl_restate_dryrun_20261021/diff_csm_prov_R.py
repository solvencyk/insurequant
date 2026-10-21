"""Read-only: CSM_waterfall_provenance.json live vs the R-without-pins package (what changes), plus the KR0073 csm_waterfall blocks as they stand."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
P = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021" / "R_nopins_package"
sys.stdout.reconfigure(encoding="utf-8")
live = json.loads((ROOT / "CSM_waterfall_provenance.json").read_text(encoding="utf-8"))
pk = json.loads((P / "CSM_waterfall_provenance.json").read_text(encoding="utf-8"))
print("top-level keys live-only:", sorted(set(live) - set(pk)), "| package-only:", sorted(set(pk) - set(live)))
for k in sorted(set(live) & set(pk)):
    if k != "cells" and live[k] != pk[k]:
        print("top-level differs:", k, "\n   live:", str(live[k])[:300], "\n   pkg :", str(pk[k])[:300])
lc = {(c["company_code"], c["quarter"], c["item_block"]): c for c in live["cells"]}
pc = {(c["company_code"], c["quarter"], c["item_block"]): c for c in pk["cells"]}
print("cells live/package:", len(lc), len(pc), "| key sets equal:", set(lc) == set(pc))
diff = [k for k in lc if lc[k] != pc.get(k)]
print("differing cells:", len(diff))
for k in sorted(diff, key=lambda x: (x[0], x[1], x[2])):
    print("  ", k, "\n     live:", json.dumps(lc[k], ensure_ascii=False)[:400], "\n     pkg :", json.dumps(pc[k], ensure_ascii=False)[:400])
print("\nKR0073 csm_waterfall blocks in live:")
for k in sorted((k for k in lc if k[0] == "KR0073"), key=lambda x: x[1]):
    c = lc[k]
    print("  ", k[1], k[2], {x: c.get(x) for x in ("source_id", "source_file", "owner_override", "published_items")})
