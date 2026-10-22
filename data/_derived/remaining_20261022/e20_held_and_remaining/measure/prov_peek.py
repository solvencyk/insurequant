import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
prov = M.jload(M.SNAP / "PL_breakdown_provenance.json")
for c in prov["cells"]:
    if c["company_code"] == sys.argv[1] and c["quarter"] in sys.argv[2].split(",") and c["item_block"] == "income_statement":
        print(json.dumps(c, ensure_ascii=False, indent=1)[:2500])
