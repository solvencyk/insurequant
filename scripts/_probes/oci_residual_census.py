import glob
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ---- 1. build KR-code -> corp_code map from existing raw meta.json (offline, no network) ----
kr_to_corp = {}
for meta_path in glob.glob("data/dart/FY*/raw/*/meta.json"):
    dirname = os.path.basename(os.path.dirname(meta_path))
    m = re.match(r"(KR\d+)_", dirname)
    if not m:
        continue
    kr = m.group(1)
    try:
        meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
    except Exception:
        continue
    cc = meta.get("corp_code")
    if cc and kr not in kr_to_corp:
        kr_to_corp[kr] = cc

print(f"resolved {len(kr_to_corp)} KR-code -> corp_code pairs from raw meta.json", file=sys.stderr)

REPRT = {"1Q": "11013", "2Q": "11012", "3Q": "11014", "4Q": "11011"}
CACHE = Path("data/dart/_fs_api_cache")

# account_ids that are OUR mapped items 25-31 (subtotal/grand-total tags — exclude from "extra
# leaf" search) plus the two intermediate reclass/non-reclass subtotal tags (also not leaves).
ACCT_OCI = {
    25: "ifrs-full_OtherComprehensiveIncome",
    26: "ifrs-full_OtherComprehensiveIncomeNetOfTaxFinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome",
    27: "ifrs-full_OtherComprehensiveIncomeNetOfTaxInsuranceFinanceIncomeExpensesFromInsuranceContractsIssuedExcludedFromProfitOrLossThatWillBeReclassifiedToProfitOrLoss",
    28: "ifrs-full_OtherComprehensiveIncomeNetOfTaxCashFlowHedges",
    29: "ifrs-full_OtherComprehensiveIncomeNetOfTaxGainsLossesFromInvestmentsInEquityInstruments",
    30: "ifrs-full_OtherComprehensiveIncomeNetOfTaxFinanceIncomeExpensesFromReinsuranceContractsHeldExcludedFromProfitOrLoss",
    31: "ifrs-full_ComprehensiveIncome",
}
SUBTOTAL_TAGS = {
    "ifrs-full_OtherComprehensiveIncomeThatWillBeReclassifiedToProfitOrLossNetOfTax",
    "ifrs-full_OtherComprehensiveIncomeThatWillNotBeReclassifiedToProfitOrLossNetOfTax",
}
MAPPED_TAGS = set(ACCT_OCI.values())


def load_cis(cc, year, reprt):
    for fs_div in ("OFS", "CFS"):
        p = CACHE / f"{cc}_{year}_{reprt}_{fs_div}.json"
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            rows = [r for r in data.get("list", []) if r.get("sj_div") == "CIS"]
            if rows:
                return rows, fs_div
    return None, None


def num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None


def ordi(r):
    """ord comes back as a STRING in the cached JSON ('12' not 12) -- lexicographic
    comparison silently corrupts any ord-window logic (e.g. '7' > '67' as strings).  Coerce."""
    o = r.get("ord")
    try:
        return int(o)
    except Exception:
        return None


# ---- 2. load PL_breakdown.json, compute residuals ----
d = json.load(open("PL_breakdown.json", encoding="utf-8"))
by_cq = defaultdict(dict)
name_by_code = {}
for r in d:
    key = (r["원보험사코드"], r["공시분기"])
    by_cq[key][r["항목번호"]] = r["값"]
    name_by_code[r["원보험사코드"]] = r["원수사명"]

cells = []
for (code, q), items in by_cq.items():
    if 25 not in items:
        continue
    comps = [items.get(i) for i in (26, 27, 28, 29, 30)]
    if any(c is None for c in comps):
        continue
    subtotal = items[25]
    comp_sum = sum(comps)
    residual = subtotal - comp_sum
    denom = max(abs(subtotal), abs(comp_sum), 1e-9)
    rel = abs(residual) / denom
    if rel <= 0.01:
        continue  # only classify the >1% residual cells
    cells.append((code, q, subtotal, comp_sum, residual, rel))

cells.sort(key=lambda x: -x[5])
print(f"classifying {len(cells)} cells with residual >1%\n")

n_resolved_by_extra_leaves = 0
n_unresolved = 0
unresolved_list = []
no_cache = []

for code, q, subtotal, comp_sum, residual, rel in cells:
    cc = kr_to_corp.get(code)
    if not cc:
        no_cache.append((code, q, "no corp_code"))
        continue
    year = q[:4]
    reprt = REPRT.get(q[5:])
    annual = q[5:] == "4Q"
    if not reprt:
        no_cache.append((code, q, "bad quarter"))
        continue
    rows, fs_div = load_cis(cc, year, reprt)
    if rows is None:
        no_cache.append((code, q, "no cache file"))
        continue

    # find item25's own value using the SAME field convention as fetch_dart_fs.py
    def field(r):
        raw = r.get("thstrm_amount") if annual else (r.get("thstrm_add_amount") or r.get("thstrm_amount"))
        return num(raw)

    # all leaf OCI rows: rows physically between item25's row (기타포괄손익 grand total) and the
    # NEXT row tagged ifrs-full_ProfitLoss (당기순이익, which always immediately follows the OCI
    # block in the K-IFRS CIS presentation).  NOTE: DART's own "ord" for ifrs-full_ComprehensiveIncome
    # (item31/총포괄손익) is NOT reliable as an upper bound -- it is frequently tagged to an EARLIER
    # ord than item25 itself (a 요약 block quirk), confirmed for 코리안리/푸본현대 both.
    ord25 = None
    pl_ords = []
    for r in rows:
        aid = r.get("account_id") or ""
        o = ordi(r)
        if aid == ACCT_OCI[25]:
            ord25 = o
        if aid == "ifrs-full_ProfitLoss" and o is not None:
            pl_ords.append(o)
    if ord25 is None:
        no_cache.append((code, q, "ord25 not found"))
        continue
    after = [o for o in pl_ords if o > ord25]
    ord_pl = min(after) if after else None
    if ord_pl is None:
        no_cache.append((code, q, f"no ProfitLoss row after ord25={ord25}"))
        continue

    leaf_sum = 0.0
    leaf_rows = []
    for r in rows:
        o = ordi(r)
        if o is None or not (ord25 < o < ord_pl):
            continue
        aid = r.get("account_id") or ""
        if aid in SUBTOTAL_TAGS or aid in (ACCT_OCI[25], ACCT_OCI[31]):
            continue
        v = field(r)
        if v is None:
            continue
        leaf_sum += v
        leaf_rows.append((r.get("account_nm"), aid, v))

    sub_v = field(next(r for r in rows if r.get("account_id") == ACCT_OCI[25]))
    if sub_v is None:
        no_cache.append((code, q, "item25 field missing"))
        continue
    # sub_v is in raw 원; compare in same unit as leaf_sum (also raw 원)
    resid2 = sub_v - leaf_sum
    rel2 = abs(resid2) / max(abs(sub_v), abs(leaf_sum), 1e-9)

    if rel2 <= 0.01:
        n_resolved_by_extra_leaves += 1
    else:
        n_unresolved += 1
        unresolved_list.append((code, name_by_code[code], q, subtotal, comp_sum, residual, rel,
                                 sub_v, leaf_sum, resid2, rel2, leaf_rows, fs_div))

print(f"resolved by summing ALL tagged CIS leaf rows between item25 and item31 (source self-consistent, schema just missing items): {n_resolved_by_extra_leaves}")
print(f"still unresolved even with all leaf rows (candidate sign-bug / other): {n_unresolved}")
print(f"no cache / lookup failure: {len(no_cache)}")

if no_cache:
    print("\n-- lookup failures (first 15) --")
    for row in no_cache[:15]:
        print(" ", row)

print("\n=== still-unresolved cells (candidate sign-bug or other cause) ===")
for code, name, q, subtotal, comp_sum, residual, rel, sub_v, leaf_sum, resid2, rel2, leaf_rows, fs_div in unresolved_list:
    print(f"\n{name}({code}) {q} [{fs_div}]: item25(백만)={subtotal:,.1f} sum26-30={comp_sum:,.1f} rel={rel:.1%}")
    print(f"   full-leaf check(원): subtotal={sub_v:,.0f}  leaf_sum={leaf_sum:,.0f}  resid={resid2:,.0f}  rel2={rel2:.1%}")
    for nm, aid, v in leaf_rows:
        print(f"     {v:>18,.0f}  {nm}  [{aid}]")
