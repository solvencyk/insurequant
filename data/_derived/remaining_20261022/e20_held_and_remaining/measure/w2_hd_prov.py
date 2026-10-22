import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
d = M.jload(M.SNAP / "PL_breakdown_provenance.json")
for c in d["cells"]:
    if c["company_code"] == "KR0009" and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"):
        print(c["quarter"], c["item_block"], c["source_id"], json.dumps(c.get("source_files"), ensure_ascii=False)[:420])
pl = M.jload(M.SNAP / "PL_breakdown.json")
for r in pl:
    if r["원보험사코드"] == "KR0009" and r["공시분기"] in ("2023.1Q", "2023.2Q") and str(r["항목번호"]) in ("1", "2", "13", "14", "15", "16"):
        print(r["공시분기"], r["항목번호"], r["항목명"], r["값"])
g = M.jload(M.SNAP / "user_pl_cells.json")
print([ (c["공시분기"], c["항목번호"], c["값"]) for c in g["set"] if c["원보험사코드"] == "KR0009"][:40])
