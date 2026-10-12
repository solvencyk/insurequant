# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
reg = json.load(open("data/bonds/capital_tier_registry.json", encoding="utf-8"))["companies"]
src = json.load(open("data/bonds/capital_securities_fy2026h1.json", encoding="utf-8"))
for c in src["companies"]:
    secs = (reg.get(c["code"]) or {}).get("securities") or []
    for b in c["bonds"]:
        if b["tier"] != "hybrid" or not b.get("outstanding_mn"):
            continue
        m = [s for s in secs if s.get("issue_date") == b.get("issue_date")]
        print(c["code"], c["company"][:8], b["issue_date"], b["outstanding_mn"] / 100, "call", b.get("call_date"),
              "->", [(s["type"], s.get("issuer_type")) for s in m] if m else ("NOMATCH registry=" + str([(s["issue_date"], s["type"]) for s in secs])))
