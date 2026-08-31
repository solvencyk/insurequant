import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

path = Path("data/dart/_fs_api_cache/00459844_2024_11014_OFS.json")
data = json.loads(path.read_text(encoding="utf-8"))
rows = data["list"]
print("total rows:", len(rows))

# group by sj_div
by_sj = Counter(r.get("sj_div") for r in rows)
print("sj_div counts:", by_sj)

cis_rows = [r for r in rows if r.get("sj_div") == "CIS"]
# check duplicate account_id within CIS
by_aid = defaultdict(list)
for r in cis_rows:
    by_aid[r.get("account_id")].append(r)

dupes = {k: v for k, v in by_aid.items() if len(v) > 1}
print("\nduplicate account_id within CIS:", len(dupes))
for aid, rs in dupes.items():
    print(f"\n=== {aid} ===")
    for r in rs:
        print(f"  ord={r.get('ord')} nm={r.get('account_nm')!r} thstrm_amount={r.get('thstrm_amount')} thstrm_add_amount={r.get('thstrm_add_amount')} bsns_year={r.get('bsns_year')} rcept_no={r.get('rcept_no')} reprt_code={r.get('reprt_code')}")

# also print reprt_code / bsns_year / thstrm_nm / frmtrm_nm for the OCI rows to understand period basis
print("\n--- period labels on OCI rows ---")
oci_ids = [
    "ifrs-full_OtherComprehensiveIncome",
    "ifrs-full_OtherComprehensiveIncomeThatWillBeReclassifiedToProfitOrLossNetOfTax",
    "dart_OtherComprehensiveIncomeNetOfTaxCreditLossesOfFinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome",
    "ifrs-full_OtherComprehensiveIncomeNetOfTaxCashFlowHedges",
    "ifrs-full_OtherComprehensiveIncomeNetOfTaxFinanceIncomeExpensesFromReinsuranceContractsHeldExcludedFromProfitOrLoss",
    "ifrs-full_OtherComprehensiveIncomeNetOfTaxFinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome",
    "ifrs-full_OtherComprehensiveIncomeNetOfTaxInsuranceFinanceIncomeExpensesFromInsuranceContractsIssuedExcludedFromProfitOrLossThatWillBeReclassifiedToProfitOrLoss",
    "ifrs-full_OtherComprehensiveIncomeThatWillNotBeReclassifiedToProfitOrLossNetOfTax",
    "ifrs-full_OtherComprehensiveIncomeNetOfTaxGainsLossesOnRemeasurementsOfDefinedBenefitPlans",
]
for r in cis_rows:
    if r.get("account_id") in oci_ids:
        print(f"ord={r.get('ord')} aid={r.get('account_id')}")
        print(f"    nm={r.get('account_nm')!r} thstrm_nm={r.get('thstrm_nm')!r} frmtrm_nm={r.get('frmtrm_nm')!r}")
        print(f"    thstrm_amount={r.get('thstrm_amount')} thstrm_add_amount={r.get('thstrm_add_amount')} frmtrm_amount={r.get('frmtrm_amount')}")
        print(f"    account_detail={r.get('account_detail')!r} currency={r.get('currency')!r}")
