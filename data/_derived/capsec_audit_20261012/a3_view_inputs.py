# -*- coding: utf-8 -*-
"""a3: print the dumped inputs as a compact table (read-only)."""
import json

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
rows = json.load(open(ROOT + "/data/_derived/capsec_audit_20261012/a2_inputs_2026_2Q.json", encoding="utf-8"))


def f(v):
    if v is None:
        return "."
    if abs(v) >= 100:
        return "%.0f" % v
    return ("%.2f" % v).rstrip("0").rstrip(".")


print("code   name            | i6 pre/post | i13 pre/post | i14 pre/post | i3 pre/post | i47 pre/post | i48 pre/post | i49 pre/post | i53 pre/post | i54 pre/post")
for code in sorted(rows):
    r = rows[code]
    cells = []
    for k in (6, 13, 14, 3, 47, 48, 49, 53, 54):
        cells.append("%s/%s" % (f(r.get("i%d_pre" % k)), f(r.get("i%d_post" % k))))
    print("%s %-10s | %s" % (code, r["name"][:8], " | ".join(cells)))
