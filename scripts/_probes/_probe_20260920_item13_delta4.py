# -*- coding: utf-8 -*-
"""Inspect the 4 over-cells that are NOT in validation's CONTAMINATED set.

For each, decide whether the over_by is (a) real TFI contamination or
(b) merely the 적용전 bridge's own baked-in residual mirrored across.
Key identity when item2_post == item2_pre (no tier movement):
    over_by == -(item4_pre - item12_pre - item13_pre - item2_pre) == -resid_pre
So a BENIGN bucket firing means the PRE bridge never closed — not contamination.
Read-only.
"""
import json, io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + os.sep
SRC = os.path.join(ROOT, "data", "_derived", "_probe_20260920_item13_deletion_set.json")
V4 = os.path.join(ROOT, "data", "_derived", "_probe_20260919_mirror_audit_v4.json")

with io.open(SRC, "r", encoding="utf-8") as f:
    P = json.load(f)
with io.open(V4, "r", encoding="utf-8") as f:
    V4ROWS = {(r["code"], r["q"]): r for r in json.load(f)["rows"]}

odd = [r for r in P["rows"] if r.get("cls_tol2_0") == "OVER" and r.get("group") != "CONTAMINATED"]
print("=== %d over-cells outside CONTAMINATED ===" % len(odd))
for r in odd:
    i2pre, i2post = r["item2_pre"], r["item2_post"]
    i4p, i12p, i13p = r["item4_pre"], r["item12_pre"], r["item13_pre_eq_post"]
    resid_pre = None
    if None not in (i4p, i12p, i13p, i2pre):
        resid_pre = round(i4p - i12p - i13p - i2pre, 2)
    tier_moved = None if None in (i2pre, i2post) else round(i2post - i2pre, 2)
    print("\n--- %s %s %s  [v4=%s]" % (r["code"], r["name"], r["q"], r["v4_verdict"]))
    print("    item2 pre=%s post=%s  (tier move Delta=%s)" % (i2pre, i2post, tier_moved))
    print("    item3 pre=%s post=%s" % (r["item3_pre"], r["item3_post"]))
    print("    item4 pre=%s post=%s | item12 pre=%s post=%s | item13 pre=post=%s"
          % (i4p, r["item4_post"], i12p, r["item12_post"], i13p))
    print("    implied13=%s  over_by=%s   resid_pre(4-12-13-2)=%s" % (r["implied13"], r["over_by"], resid_pre))
    v = V4ROWS.get((r["code"], r["q"]))
    if v:
        for k in ("verdict", "reason", "tfi", "src", "delta", "resid_pre", "resid_post",
                  "row_pre", "row_post", "md_line", "pdf_page", "note"):
            if k in v:
                print("    v4.%s = %s" % (k, v[k]))

# also: how many CONTAMINATED-bucket item13 cells did NOT fire?
con = [r for r in P["rows"] if r.get("v4_verdict") == "CONTAMINATED"]
print("\n=== CONTAMINATED buckets with mirrored item13: %d ; fired(tol2.0)=%d ===" %
      (len(con), sum(1 for r in con if r.get("cls_tol2_0") == "OVER")))
for r in con:
    if r.get("cls_tol2_0") != "OVER":
        print("   NOT fired: %s %s %s over_by=%s cls=%s" %
              (r["code"], r["name"], r["q"], r.get("over_by"), r.get("cls_tol2_0")))

nb = [r for r in P["rows"] if r.get("cls") == "NOT_BACKCOMPUTABLE"]
print("\n=== not back-computable mirrored item13 cells: %d ===" % len(nb))
for r in nb:
    print("   %s %s %s v4=%s item4_pre=%s item12_pre=%s item2_post=%s" %
          (r["code"], r["name"], r["q"], r["v4_verdict"], r["item4_pre"], r["item12_pre"], r["item2_post"]))
