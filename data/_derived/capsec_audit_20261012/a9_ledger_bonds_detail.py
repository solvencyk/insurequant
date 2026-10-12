# -*- coding: utf-8 -*-
"""a9: list the ledger bonds (subordinated + hybrid) for selected companies with recognition rate at 2026-06-30
(Ⅲ.3.다.(2)① 잔존만기 5년 미만부터 매년 20%p 차감; my own implementation of the regulation sentence, not the repo helper). Read-only."""
import json
import math
import sys
from datetime import date

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
doc = json.load(open(ROOT + "/data/bonds/capital_securities_fy2026h1.json", encoding="utf-8"))
AS_OF = date(2026, 6, 30)


def rate(maturity_iso):
    if not maturity_iso:
        return 1.0
    y, m, d = (int(x) for x in maturity_iso.split("-"))
    yrs = (date(y, m, d) - AS_OF).days / 365.25
    if yrs >= 5:
        return 1.0
    if yrs <= 0:
        return 0.0
    return max(0.0, 1.0 - 0.20 * math.ceil(5 - yrs))


codes = sys.argv[1:]
for c in doc["companies"]:
    if codes and c["code"] not in codes:
        continue
    print("==", c["code"], c.get("company"), "as_of", c.get("as_of"), "bs_sub", c.get("bs_subordinated_mn"), "bs_hyb", c.get("bs_hybrid_mn"))
    tot_leg = tot_leg_rec = tot_new = tot_new_rec = 0.0
    for b in c["bonds"]:
        out = (b.get("outstanding_mn") or 0) / 100.0
        iss = b.get("issue_date") or ""
        legacy = bool(iss) and iss < "2023-01-01"
        rr = rate(b.get("legal_maturity")) if b.get("tier") == "subordinated" else 1.0
        print("  %-12s %-10s iss=%s call=%s mat=%s out=%8.1f rate=%.1f rec=%8.1f asof=%s %s" % (
            b.get("tier"), "LEGACY" if legacy else "new/unk", iss, b.get("call_date"), b.get("legal_maturity"), out, rr, out * rr, b.get("as_of"),
            (b.get("name") or "")[:40]))
        if b.get("tier") == "subordinated":
            if legacy:
                tot_leg += out
                tot_leg_rec += out * rr
            else:
                tot_new += out
                tot_new_rec += out * rr
    print("  -> legacy sub out %.1f rec %.1f | new sub out %.1f rec %.1f" % (tot_leg, tot_leg_rec, tot_new, tot_new_rec))
