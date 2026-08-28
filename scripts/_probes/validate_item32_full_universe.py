"""Full-universe validation for item32 (기타 포괄손익(미분류)).

For every (code, quarter) in PL_breakdown.json that has item25 present, resolve corp_code
BY NAME (fetch_dart_fs.resolve_corp -- offline via the local CORPCODE.xml master, broader
coverage than the old census's raw-meta.json lookup), call tier1_for() fresh (reads only
data/dart/_fs_api_cache/, no network, no raw XML), and cross-check:

    item25 == item26 + item27 + item28 + item29 + item30 + item32

using the EXISTING (current, post-override) values for items 25-31 already in PL_breakdown.json
-- NOT recomputed -- so this measures "does adding item32, as computed by the new
_oci32_from_rows, close the identity against what's already on the master (including the
KR0083 sign-flip fix already applied)".

Offline. Does not write anything.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import resolve_corp, tier1_for  # noqa: E402

d = json.load(open("PL_breakdown.json", encoding="utf-8"))
by_cq = defaultdict(dict)
name_by_code = {}
for r in d:
    key = (r["원보험사코드"], r["공시분기"])
    by_cq[key][r["항목번호"]] = r["값"]
    name_by_code[r["원보험사코드"]] = r["원수사명"]

targets = [(code, q) for (code, q), items in by_cq.items() if 25 in items and items[25] is not None]
print(f"total (code,q) with item25 present (non-null): {len(targets)}")

no_corp = []       # name -> corp_code resolution failed
no_t1 = []         # tier1_for() returned nothing usable
no_item25_t1 = []  # tier1_for() ok but no fresh item25 (shouldn't happen if master had it)
reconciled = []    # <=1%
close = []         # 1-5%
unresolved = []    # >5%
skipped_missing_term = []  # one of 26-30 is None on the (unchanged) master -> can't evaluate

for code, q in sorted(targets):
    name = name_by_code[code]
    cc = resolve_corp(name)
    if not cc:
        no_corp.append((code, name, q))
        continue
    t1 = tier1_for(name, q, code)
    if not t1:
        no_t1.append((code, name, q))
        continue
    v32 = t1.get(32)
    items = by_cq[(code, q)]
    it25 = items.get(25)
    parts_keys = (26, 27, 28, 29, 30)
    parts = [items.get(k) for k in parts_keys]
    if any(p is None for p in parts):
        skipped_missing_term.append((code, name, q, [k for k, p in zip(parts_keys, parts) if p is None]))
        continue
    if v32 is None:
        # item32 itself absent (source gap, e.g. 삼성화재) -- also can't evaluate the full identity
        skipped_missing_term.append((code, name, q, [32]))
        continue
    total = sum(parts) + v32
    resid = it25 - total
    rel = abs(resid) / max(abs(it25), abs(total), 1e-9)
    row = (code, name, q, it25, total, resid, rel, v32)
    if rel <= 0.01:
        reconciled.append(row)
    elif rel <= 0.05:
        close.append(row)
    else:
        unresolved.append(row)

print(f"no corp_code resolved (name search failed): {len(no_corp)}")
for x in no_corp:
    print(f"   {x}")
print(f"tier1_for() returned nothing (no cache / no income statement): {len(no_t1)}")
for x in no_t1[:20]:
    print(f"   {x}")
print(f"skipped (26-30 or 32 has a None term on current master): {len(skipped_missing_term)}")
by_reason = defaultdict(int)
for code, name, q, missing in skipped_missing_term:
    by_reason[(code, name)] += 1
for (code, name), n in sorted(by_reason.items(), key=lambda x: -x[1]):
    print(f"   {code} {name}: {n} quarters")

evaluated = len(reconciled) + len(close) + len(unresolved)
print(f"\nEVALUATED (all of 26,27,28,29,30,32 present): {evaluated}")
print(f"  reconciled (<=1%): {len(reconciled)}  ({len(reconciled)/max(evaluated,1)*100:.1f}%)")
print(f"  close (1-5%):      {len(close)}")
print(f"  unresolved (>5%):  {len(unresolved)}")

print("\n=== unresolved (>5%) ===")
for code, name, q, it25, total, resid, rel, v32 in unresolved:
    print(f"  {name}({code}) {q}: item25={it25:,.3f}  sum(26-30,32)={total:,.3f}  "
          f"resid={resid:,.3f}  rel={rel:.1%}  item32={v32:,.3f}")

print("\n=== close (1-5%) ===")
for code, name, q, it25, total, resid, rel, v32 in close:
    print(f"  {name}({code}) {q}: item25={it25:,.3f}  sum(26-30,32)={total:,.3f}  "
          f"resid={resid:,.3f}  rel={rel:.1%}  item32={v32:,.3f}")
