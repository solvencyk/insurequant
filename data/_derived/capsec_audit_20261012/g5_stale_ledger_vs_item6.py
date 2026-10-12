# -*- coding: utf-8 -*-
"""g5: for every company whose bond ledger is still as_of 2025-12-31, compare the ledger's hybrid+sub totals with the K-ICS 2026.2Q figures
(item 6 = 자본항목 중 보통주 이외 자본증권; item 53/54 = 경과조치 기발행 신종/후순위) - a gap means an H1-2026 issuance/redemption the ledger does not know.
Independent: pinned ledger + my own dump of the master.   Output g5_stale_ledger_vs_item6_<rev>.txt"""
import json
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
led = audit_io.load_json("data/bonds/capital_securities_fy2026h1.json")["companies"]
inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
L = ["PIN rev=%s ledger=%s" % (audit_io.resolved_rev(), audit_io.sha12("data/bonds/capital_securities_fy2026h1.json"))]
stale = [c for c in led if c.get("as_of") == "2025-12-31"]
fresh = [c for c in led if c.get("as_of") != "2025-12-31"]
L.append("ledger rows: %d as_of 2025-12-31 (carried forward from the FY2025 annual report), %d as_of 2026-06-30 (H1 2026)" % (len(stale), len(fresh)))
L.append("columns: code name | ledger hybrid (억, face) | K-ICS item 6 (억, 2026.2Q 값) | gap | ledger sub (억) | K-ICS item 54 (억) ; gap flags |gap| > 2% of item 6 or > 50억")
n_gap = 0
for grp, nm in ((stale, "STALE (2025-12-31)"), (fresh, "FRESH (2026-06-30)")):
    L.append("-- " + nm)
    for c in grp:
        code = c["code"]
        r = inp.get(code, {})
        hy = (c.get("total_hybrid_outstanding_mn") or 0) / 100.0
        sb = (c.get("total_subordinated_outstanding_mn") or 0) / 100.0
        i6 = r.get("i6_pre")
        i54 = r.get("i54_pre")
        gap = None if i6 is None else hy - i6
        flag = ""
        if gap is not None and (abs(gap) > 50 and abs(gap) > 0.02 * max(abs(i6), 1.0)):
            flag = "  <== GAP"
            n_gap += 1
        L.append("  %s %s | hybrid %.0f | item6 %s | gap %s | sub %.0f | item54 %s%s" % (
            code, c["company"], hy, "-" if i6 is None else "%.0f" % i6, "-" if gap is None else "%+.0f" % gap, sb, "-" if i54 is None else "%.0f" % i54, flag))
L.append("")
L.append("companies flagged: %d (item 6 also contains preferred / convertible-preferred shares that are not in the bond ledger - a gap is a prompt to look, not proof)" % n_gap)
open(HERE + "g5_stale_ledger_vs_item6" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
