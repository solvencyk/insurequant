import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

TARGET = "ifrs-full_OtherComprehensiveIncomeNetOfTaxFinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome"

d = json.loads(Path("data/dart/_fs_api_cache/00104069_2026_11012_OFS.json").read_text(encoding="utf-8"))
count = 0
for a in d.get("list", []):
    aid = a.get("account_id") or ""
    if aid == TARGET:
        count += 1
        print(a.get("sj_div"), a.get("ord"), repr(aid), a.get("account_nm"),
              a.get("thstrm_amount"), a.get("thstrm_add_amount"))
print("exact matches:", count)
print("len(aid) target:", len(TARGET))

# also print every distinct account_id length near this, in case of a hidden char
for a in d.get("list", []):
    aid = a.get("account_id") or ""
    if aid.startswith("ifrs-full_OtherComprehensiveIncomeNetOfTaxFinancialAssets"):
        print("PARTIAL:", a.get("sj_div"), repr(aid), len(aid))
