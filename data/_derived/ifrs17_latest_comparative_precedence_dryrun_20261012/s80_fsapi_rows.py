"""Read-only: dump FS-API cache income-statement rows (account_nm, sj_div, thstrm/frmtrm amounts) that mention a keyword, for one corp/year/reprt.
usage: python s80_fsapi_rows.py KR0001 2024 11013 [keyword ...]"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
kr, year, reprt = sys.argv[1:4]
kws = sys.argv[4:] or ["사업비용", "영업", "보험손익", "손익"]
corp = None
for fy in sorted((ROOT / "data/dart").glob("FY*_Q*")):
    for d in (fy / "raw").glob(f"{kr}_*"):
        mp = d / "meta.json"
        if mp.exists():
            corp = json.loads(mp.read_text(encoding="utf-8")).get("corp_code")
            break
    if corp:
        break
print("corp", corp)
for div in ("OFS", "CFS"):
    f = ROOT / "data/dart/_fs_api_cache" / f"{corp}_{year}_{reprt}_{div}.json"
    if not f.exists():
        continue
    d = json.loads(f.read_text(encoding="utf-8"))
    print("=" * 90, f.name, "status", d.get("status"), "rows", len(d.get("list", [])))
    for a in d.get("list", []):
        if a.get("sj_div") not in ("IS", "CIS"):
            continue
        nm = a.get("account_nm", "")
        if any(k in nm for k in kws):
            print(f"  {a.get('sj_div')} ord={a.get('ord')} {nm[:34]:<34} thstrm={a.get('thstrm_amount')!s:>16} add={a.get('thstrm_add_amount')!s:>16} | frmtrm={a.get('frmtrm_amount')!s:>16} fadd={a.get('frmtrm_add_amount')!s:>16} id={a.get('account_id', '')[:40]}")
