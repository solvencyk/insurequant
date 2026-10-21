import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
R = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/dart/_fs_api_cache")
for name in sys.argv[1:]:
    d = json.loads((R / name).read_text(encoding="utf-8"))
    rows = d.get("list", [])
    print(name, "status", d.get("status"), "rows", len(rows), "keys", sorted(rows[0].keys()) if rows else None)
    for a in rows:
        if a.get("sj_div") in ("IS", "CIS") and a.get("account_id") in ("ifrs-full_InsuranceServiceResult", "ifrs-full_ProfitLoss", "ifrs-full_ProfitLossBeforeTax"):
            print("  ", a.get("sj_div"), a.get("account_id"), a.get("account_nm"), "| thstrm", a.get("thstrm_amount"), "| thstrm_add", a.get("thstrm_add_amount"), "| frmtrm", a.get("frmtrm_amount"), "| frmtrm_add", a.get("frmtrm_add_amount"))
