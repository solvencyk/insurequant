"""k1: KR0104 master dump (PL + CSM + provenance + gold) for 2023.1Q-2024.1Q (READ-ONLY, snapshot)."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

sys.stdout.reconfigure(encoding="utf-8")
CODE = sys.argv[1] if len(sys.argv) > 1 else "KR0104"
QS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"]
pl, names, inames = M.load_pl()
dg = M.load_pl_dangi()
print(CODE, names.get(CODE))
hdr = "item name".ljust(30) + "".join(q.rjust(16) for q in QS)
print(hdr)
for it in range(1, 33):
    row = f"{it:>2} {inames.get(it, '')[:26]:<27}"
    for q in QS:
        v = pl.get((CODE, q), {}).get(it)
        row += (f"{v:16,.3f}" if v is not None else "            None")
    print(row)
print("--- 값_당분기")
for it in (1, 2, 3, 8, 15, 16, 17, 20, 22, 24):
    row = f"{it:>2} {inames.get(it, '')[:26]:<27}"
    for q in QS:
        v = dg.get((CODE, q), {}).get(it)
        row += (f"{v:16,.3f}" if v is not None else "            None")
    print(row)

# provenance
prov = M.jload(M.SNAP / "PL_breakdown_provenance.json")
for c in prov["cells"]:
    if c["company_code"] == CODE and c["quarter"] in QS:
        print("PROV", c["quarter"], c["item_block"], c.get("source_id"), c.get("resolution"), "owner_override=" + str(c.get("owner_override")))
        for sf in c.get("source_files", []):
            print("      ", sf.get("how"), sf.get("file"), sf.get("items"))
# gold overlay
gold = M.jload(M.SNAP / "user_pl_cells.json")
print("gold keys", list(gold.keys())[:10] if isinstance(gold, dict) else type(gold))
