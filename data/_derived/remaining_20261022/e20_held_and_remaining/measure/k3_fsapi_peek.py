"""k3: peek into a FS-API cache file (READ-ONLY)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
C = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/dart/_fs_api_cache")
name = sys.argv[1]
d = json.loads((C / name).read_text(encoding="utf-8"))
print(type(d), list(d.keys()) if isinstance(d, dict) else len(d))
lst = d.get("list") if isinstance(d, dict) else d
print("status", d.get("status") if isinstance(d, dict) else None, "n", len(lst or []))
if lst:
    print(json.dumps(lst[0], ensure_ascii=False)[:800])
    for r in lst:
        if r.get("sj_div") in ("CIS", "IS"):
            print(r.get("sj_div"), r.get("account_id"), "|", r.get("account_nm"), "|", r.get("thstrm_amount"), "|", r.get("thstrm_add_amount"), "|", r.get("frmtrm_amount"), "|", r.get("frmtrm_add_amount") if "frmtrm_add_amount" in r else "")
