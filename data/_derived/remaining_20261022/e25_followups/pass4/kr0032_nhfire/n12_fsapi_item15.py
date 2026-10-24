# -*- coding: utf-8 -*-
"""READ-ONLY: does the FS-API cache of NH농협손보 (corp 00908155, 별도 OFS) carry a 기타영업수익 account?  Prints, per cached response, the number of accounts, the number of accounts named 기타영업수익
(expected 0) and the prior-cumulative (frmtrm_add) amounts of the accounts used by the ticket (보험손익, 기타사업비용, 투자손익, 영업이익) - an independent second source for the printed comparative columns."""
import glob
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
for f in sorted(glob.glob(f"{ROOT}/data/dart/_fs_api_cache/00908155_202[34]_*_OFS.json")):
    d = json.load(open(f, encoding="utf-8"))
    lst = d.get("list") if isinstance(d, dict) else d
    name = f.replace("\\", "/").split("/")[-1]
    if not lst:
        print(f"===== {name}: status {d.get('status')} (no data)")
        continue
    n15 = [r for r in lst if "기타영업수익" in r.get("account_nm", "")]
    print(f"===== {name}: status {d.get('status')}, accounts {len(lst)}, accounts named 기타영업수익 (the id dart_OtherOperatingIncomeInvestment is 기타투자수익, a different line): {len(n15)}")
    for r in lst:
        nm = r.get("account_nm", "")
        if "기타사업비용" in nm or nm.replace(" ", "") in ("보험손익", "투자손익", "영업이익"):
            print("   ", r.get("sj_div"), r.get("account_id"), "|", nm, "| thstrm", r.get("thstrm_amount"), "| frmtrm_add", r.get("frmtrm_add_amount"), "| frmtrm", r.get("frmtrm_amount"))
