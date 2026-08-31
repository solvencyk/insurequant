import glob
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

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

REPRT = {"1Q": "11013", "2Q": "11012", "3Q": "11014", "4Q": "11011"}
CACHE = Path("data/dart/_fs_api_cache")
ACCT_OCI25 = "ifrs-full_OtherComprehensiveIncome"
ACCT_OCI31 = "ifrs-full_ComprehensiveIncome"
SUBTOTAL_TAGS = {
    "ifrs-full_OtherComprehensiveIncomeThatWillBeReclassifiedToProfitOrLossNetOfTax",
    "ifrs-full_OtherComprehensiveIncomeThatWillNotBeReclassifiedToProfitOrLossNetOfTax",
}


def ordi(r):
    try:
        return int(r.get("ord"))
    except Exception:
        return None


def num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None


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


d = json.load(open("PL_breakdown.json", encoding="utf-8"))
by_cq = defaultdict(dict)
name_by_code = {}
for r in d:
    key = (r["원보험사코드"], r["공시분기"])
    by_cq[key][r["항목번호"]] = r["값"]
    name_by_code[r["원보험사코드"]] = r["원수사명"]

targets = [(code, q) for (code, q), items in by_cq.items() if 25 in items]
print(f"total (code,q) with item25 present: {len(targets)}")

no_lookup = 0
reconciled = 0
close = []       # 1-5%
unresolved = []  # >5%

for code, q in targets:
    cc = kr_to_corp.get(code)
    if not cc:
        no_lookup += 1
        continue
    year = q[:4]
    reprt = REPRT.get(q[5:])
    annual = q[5:] == "4Q"
    if not reprt:
        no_lookup += 1
        continue
    rows, fs_div = load_cis(cc, year, reprt)
    if rows is None:
        no_lookup += 1
        continue

    def field(r):
        raw = r.get("thstrm_amount") if annual else (r.get("thstrm_add_amount") or r.get("thstrm_amount"))
        return num(raw)

    ord25 = None
    pl_ords = []
    sub_v = None
    for r in rows:
        aid = r.get("account_id") or ""
        o = ordi(r)
        if aid == ACCT_OCI25:
            ord25 = o
            sub_v = field(r)
        if aid == "ifrs-full_ProfitLoss" and o is not None:
            pl_ords.append(o)
    if ord25 is None or sub_v is None:
        no_lookup += 1
        continue
    after = [o for o in pl_ords if o > ord25]
    ord_pl = min(after) if after else None
    if ord_pl is None:
        no_lookup += 1
        continue

    leaf_sum = 0.0
    leaf_rows = []
    for r in rows:
        o = ordi(r)
        if o is None or not (ord25 < o < ord_pl):
            continue
        aid = r.get("account_id") or ""
        if aid in SUBTOTAL_TAGS or aid in (ACCT_OCI25, ACCT_OCI31):
            continue
        v = field(r)
        if v is None:
            continue
        leaf_sum += v
        leaf_rows.append((r.get("account_nm"), aid, v))

    resid = sub_v - leaf_sum
    rel = abs(resid) / max(abs(sub_v), abs(leaf_sum), 1e-9)
    if rel <= 0.01:
        reconciled += 1
    elif rel <= 0.05:
        close.append((code, name_by_code[code], q, fs_div, sub_v, leaf_sum, resid, rel, leaf_rows))
    else:
        unresolved.append((code, name_by_code[code], q, fs_div, sub_v, leaf_sum, resid, rel, leaf_rows))

print(f"no corp/cache lookup: {no_lookup}")
print(f"reconciled (<=1%) via full leaf-sum: {reconciled}")
print(f"close (1-5%): {len(close)}")
print(f"unresolved (>5%): {len(unresolved)}")

print("\n=== unresolved (>5%) cases -- candidates for genuine sign-flip / real gap ===")
for code, name, q, fs_div, sub_v, leaf_sum, resid, rel, leaf_rows in unresolved:
    print(f"\n{name}({code}) {q} [{fs_div}]: subtotal={sub_v:,.0f}  leaf_sum={leaf_sum:,.0f}  resid={resid:,.0f}  rel={rel:.1%}")
    for nm, aid, v in leaf_rows:
        print(f"     {v:>18,.0f}  {nm}  [{aid}]")

print("\n=== close (1-5%) cases ===")
for code, name, q, fs_div, sub_v, leaf_sum, resid, rel, leaf_rows in close:
    print(f"{name}({code}) {q} [{fs_div}]: subtotal={sub_v:,.0f}  leaf_sum={leaf_sum:,.0f}  resid={resid:,.0f}  rel={rel:.1%}")
