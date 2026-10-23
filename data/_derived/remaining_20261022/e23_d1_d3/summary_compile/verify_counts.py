# -*- coding: utf-8 -*-
"""Read-only cross-check of the counts quoted in the ticket answer: live masters vs git HEAD, by company.

Also re-computes the KDB basis-mix arithmetic from the live PL master (sum of the four 2023 single quarters minus
the annual cumulative, items 17/18/20/22/24/31) and the gold / ledger sizes.
"""
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
TARGET = ["KR0099", "KR0003", "KR0070", "KR0009", "KR0072"]


def head_json(rel: str):
    out = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout
    return json.loads(out.decode("utf-8"))


def live_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def index(rows):
    return {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}


def same(a, b):
    if a is None or b is None:
        return a is b
    return abs(a - b) <= 1e-9


for rel in ["PL_breakdown.json", "CSM_waterfall.json"]:
    h, l = head_json(rel), live_json(rel)
    hi, li = index(h), index(l)
    print(f"== {rel}: rows head {len(h)} live {len(l)}; keys only in head {len(set(hi) - set(li))} only in live {len(set(li) - set(hi))}")
    val, dan, other = Counter(), Counter(), Counter()
    for k, r in li.items():
        o = hi.get(k)
        if o is None:
            continue
        if not same(o.get("값"), r.get("값")):
            val[k[0]] += 1
        if not same(o.get("값_당분기"), r.get("값_당분기")):
            dan[k[0]] += 1
        for f in r:
            if f not in ("값", "값_당분기") and r.get(f) != o.get(f):
                other[(k[0], f)] += 1
    print("   값 changed by company     :", {c: val[c] for c in sorted(val)}, "total", sum(val.values()))
    print("   값_당분기 changed by company:", {c: dan[c] for c in sorted(dan)}, "total", sum(dan.values()))
    print("   other fields changed       :", dict(other) or "none")
    outside = [c for c in set(val) | set(dan) if c not in TARGET]
    print("   companies outside the five :", outside or "none")
    quarters = Counter(k[2] for k, r in li.items() if k[0] in TARGET and k in hi and (not same(hi[k].get("값"), r.get("값")) or not same(hi[k].get("값_당분기"), r.get("값_당분기"))))
    print("   quarters touched           :", dict(sorted(quarters.items())))

# KDB basis-mix arithmetic from the live PL master
pl = index(live_json("PL_breakdown.json"))
print("== KR0072 live PL: single-quarter sum minus annual cumulative (백만원)")
for item in (17, 18, 20, 22, 24, 31, 1, 2, 3):
    singles = [pl.get(("KR0072", item, q), {}).get("값_당분기") for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q")]
    annual = pl.get(("KR0072", item, "2023.4Q"), {}).get("값")
    if None in singles or annual is None:
        print(f"   item {item:>2}: incomplete {singles} annual {annual}")
    else:
        print(f"   item {item:>2}: sum {sum(singles):.6f} annual {annual:.6f} diff {sum(singles) - annual:.6f}")
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    r = pl.get(("KR0072", 17, q), {})
    print(f"   item 17 {q}: cum {r.get('값')} single {r.get('값_당분기')}")

# gold / ledger sizes
g_pl = live_json("data/_gold/user_pl_cells.json")
g_csm = live_json("data/_gold/user_csm_cells.json")
led = live_json("data/_gold/gold_overlay_ledger.json")
def size(d):
    return {k: (len(v) if hasattr(v, "__len__") else v) for k, v in d.items()} if isinstance(d, dict) else len(d)
print("== gold PL top-level sizes :", size(g_pl))
print("== gold CSM top-level sizes:", size(g_csm))
print("== ledger top-level sizes  :", size(led))
