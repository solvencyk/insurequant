# -*- coding: utf-8 -*-
"""a5: print every dumped item (pre/post) for the codes given on the command line (read-only)."""
import json
import sys

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
rows = json.load(open(ROOT + "/data/_derived/capsec_audit_20261012/a2_inputs_2026_2Q.json", encoding="utf-8"))
ITEMS = [1, 2, 3, 6, 13, 14, 15, 27, 28, 47, 48, 49, 50, 51, 52, 53, 54]
for code in sys.argv[1:]:
    r = rows[code]
    print("==", code, r["name"], r["type"])
    for k in ITEMS:
        print("  item %-3d pre=%-12s post=%s" % (k, r.get("i%d_pre" % k), r.get("i%d_post" % k)))
