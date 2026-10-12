# -*- coding: utf-8 -*-
"""h0: what changed in kics_disclosure.json between the pinned audit state (dbbffcb5) and the new pin?  Cell-level diff on (company, quarter, item).
Relevant here: any change in a 2026.2Q cell of items 1,2,3,6,13,14,15,27,28,47-54, and any change in other quarters of items used by the forward/census checks.
Output h0_master_diff_<newrev>.txt"""
import json
import sys
from collections import Counter

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

OLD = "dbbffcb5"
NEW = audit_io.resolved_rev()
old = audit_io.load_json("kics_disclosure.json", OLD)
new = audit_io.load_json("kics_disclosure.json", NEW)


def key(r):
    return (r["원보험사코드"], r["공시분기"], r["항목번호"])


def vals(r):
    return (r.get("값"), r.get("값_적용후"), r.get("값_당분기") if "값_당분기" in r else None)


o = {key(r): r for r in old}
n = {key(r): r for r in new}
L = ["old %s rows %d ; new %s rows %d" % (OLD, len(old), NEW, len(new))]
added = sorted(set(n) - set(o))
removed = sorted(set(o) - set(n))
changed = [k for k in sorted(set(o) & set(n)) if (o[k].get("값"), o[k].get("값_적용후")) != (n[k].get("값"), n[k].get("값_적용후"))]
L.append("rows added %d, removed %d, value-changed %d" % (len(added), len(removed), len(changed)))
c = Counter((k[1], k[2]) for k in changed)
L.append("changed by (quarter,item): " + ", ".join("%s/%s:%d" % (q, i, v) for (q, i), v in sorted(c.items())))
L.append("changed by company: " + ", ".join("%s:%d" % (co, v) for co, v in sorted(Counter(k[0] for k in changed).items())))
L.append("--- 2026.2Q changes (all items):")
for k in changed:
    if k[1] == "2026.2Q":
        L.append("   %s %s item %s : %s/%s -> %s/%s" % (k[0], k[1], k[2], o[k].get("값"), o[k].get("값_적용후"), n[k].get("값"), n[k].get("값_적용후")))
L.append("--- added rows (first 40):")
for k in added[:40]:
    L.append("   %s %s item %s : %s/%s" % (k[0], k[1], k[2], n[k].get("값"), n[k].get("값_적용후")))
L.append("--- removed rows (first 20): %s" % removed[:20])
L.append("--- other-quarter changes of items 1,2,3,6,13,14,27,28,47..54 (first 60):")
cnt = 0
for k in changed:
    if k[1] != "2026.2Q" and k[2] in (1, 2, 3, 6, 13, 14, 27, 28, 47, 48, 49, 50, 51, 52, 53, 54):
        cnt += 1
        if cnt <= 60:
            L.append("   %s %s item %s : %s/%s -> %s/%s" % (k[0], k[1], k[2], o[k].get("값"), o[k].get("값_적용후"), n[k].get("값"), n[k].get("값_적용후")))
L.append("count of such cells: %d" % cnt)
open(HERE + "h0_master_diff_%s.txt" % NEW, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L[:70]))
