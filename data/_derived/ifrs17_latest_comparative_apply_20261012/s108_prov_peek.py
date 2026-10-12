"""Read-only: print PL_breakdown_provenance records of one company/quarter.
usage: s108_prov_peek.py <KRcode> <quarter>"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
code, q = sys.argv[1], sys.argv[2]
prov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
for c in prov["cells"]:
    if c["company_code"] == code and c["quarter"] == q:
        print(json.dumps(c, ensure_ascii=False, indent=1)[:3000])
        print("-----")
