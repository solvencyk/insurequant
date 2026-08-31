import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

path = Path("data/dart/_fs_api_cache/00459844_2024_11014_OFS.json")
data = json.loads(path.read_text(encoding="utf-8"))

print(type(data), list(data.keys()) if isinstance(data, dict) else len(data))

# figure out the list of rows
if isinstance(data, dict):
    rows = data.get("list") or data.get("data") or data
else:
    rows = data

print("n rows:", len(rows) if hasattr(rows, "__len__") else "?")
if isinstance(rows, list) and rows:
    print("sample row keys:", list(rows[0].keys()))

# Filter CIS rows (sj_div == 'CIS')
cis_rows = [r for r in rows if isinstance(r, dict) and r.get("sj_div") == "CIS"]
print("\nCIS rows count:", len(cis_rows))
for r in cis_rows:
    print("---")
    for k in ("account_id", "account_nm", "thstrm_amount", "thstrm_add_amount", "ord", "fs_div"):
        print(f"  {k}: {r.get(k)}")
