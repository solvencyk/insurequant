"""Read-only dry run: items 10-15 of KR0073 2023.4Q on the FY2024 annual prior-year-end (restated) column, same engine as
scripts/unify_ilp_restated_3cells_2023_4q.py (cur/prior swapped).  Writes nothing except the report in this folder."""
import sys, json
from pathlib import Path
REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import extract_insurance_liability_lic as lic
import load_ilp_latest3_2023_4q as L3
import load_ilp_backfill_pre2025 as L
import unify_ilp_restated_3cells_2023_4q as U
L3.BS_UNIT_TO_EOK["KR0073"] = 1e-8   # statement printed in won
lic.QMAP.update({"FY2023_Q4": "2023.4Q", "FY2024_Q4": "2024.4Q"})
code = "KR0073"
rec, liab, asset, bsfile = U.build(code)
print("status", rec["status"], rec.get("reason"), rec.get("flags"), "class", rec.get("class"))
print("bs prior col liab_eok/asset_eok", liab, asset, bsfile)
new = lic.cell_item_values(rec) if rec["status"] == "loaded" else None
print("new", new)
ilp = L.load(L.ILP)
old = {r["항목번호"]: r["값"] for r in ilp if r["원보험사코드"] == code and r["공시분기"] == "2023.4Q"}
print("old", {k: old[k] for k in sorted(old)})
if new:
    print("check 15-10-14", round(new[15] - new[10] - new[14], 2), " 15-bs_liab", round(new[15] - liab, 2))
    print("tables", [(t["i"], bool(t["kept"]), round(t["tot_mm"] / 100, 2)) for t in rec["tables"]])
