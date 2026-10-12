# -*- coding: utf-8 -*-
"""Request 8 probe (owner decision 2026-10-12 night): tier2 numerator deducts only pre-2023 issuance.
Read-only. For every company: printed item 53 / 54, ledger pre-2023 hybrid / sub outstanding, as_of, current rule/numerator."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")
import capital_utilization_rules as R

recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
ledger = R.load_ledger()
registry = R.load_registry()
comp = R.compute_quarter(recs, "2026.2Q", ledger, registry)
rows = json.loads((ROOT / "kics_capital_securities.json").read_text(encoding="utf-8"))["rows"]
leg = {}
for r in rows:
    e = leg.setdefault(r["원보험사코드"], {"h": 0.0, "s": 0.0, "h_all": 0.0, "s_all": 0.0, "asof": set()})
    pre = (r.get("발행일") or "") < "2023-01-01"
    bal = r.get("잔액_억") or 0.0
    k = "h" if r["종류"] == "신종자본증권" else "s"
    e[k + "_all"] += bal
    if pre: e[k] += bal
    if r.get("잔액기준일"): e["asof"].add(r["잔액기준일"])
print("code name | p53 p54 | ledger_pre23 hyb sub | ledger_all hyb sub | asof | rule num pct")
for code, c in comp.items():
    t2 = c["t2"]; e = leg.get(code, {"h": 0, "s": 0, "h_all": 0, "s_all": 0, "asof": set()})
    p53, p54 = c["item53"] or 0.0, c["item54"] or 0.0
    flag = ""
    if p53 > 2 and e["h"] + 2 < p53: flag += " H<"
    if p54 > 2 and e["s"] + 2 < p54: flag += " S<"
    if p53 or p54 or e["h"] or e["s"]:
        print(f"{code} {str(c['name'])[:8]:8s} | {p53:9.1f} {p54:9.1f} | {e['h']:9.1f} {e['s']:9.1f} | {e['h_all']:9.1f} {e['s_all']:9.1f} | {','.join(sorted(e['asof']))} | {t2['rule']} {t2['numerator']} {t2['pct']}{flag}")
