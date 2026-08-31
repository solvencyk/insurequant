import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
rows = data["list"]
cis_rows = [r for r in rows if r.get("sj_div") == "CIS"]
print(f"CIS rows: {len(cis_rows)}  (file={path.name})")
for r in cis_rows:
    nm = r.get("account_nm") or ""
    if "포괄" in nm or "재측정" in nm or "환산" in nm or "지분법" in nm:
        print(f"ord={r.get('ord'):>3} aid={r.get('account_id')}")
        print(f"    nm={nm!r}")
        print(f"    thstrm_amount={r.get('thstrm_amount'):>18}  thstrm_add_amount={r.get('thstrm_add_amount')}")
