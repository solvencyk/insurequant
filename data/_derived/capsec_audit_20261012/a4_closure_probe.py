# -*- coding: utf-8 -*-
"""a4: probe how item 47 / 48 / 49 / 53 / 54 close against the issuer's own 보완자본 (item 3).

Read-only exploration for the independent tier2 recompute. No imports from scripts/ or src/.
closure residual:  R = item3_post - item49 - item54 - max(0, item53 - 0.15*SCR_pre) - min(N, item48)
printed for N = item47_post and N = item47_pre-53-54 variants, so the print conventions of each issuer are visible.
"""
import json

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
rows = json.load(open(ROOT + "/data/_derived/capsec_audit_20261012/a2_inputs_2026_2Q.json", encoding="utf-8"))


def g(r, k, default=0.0):
    v = r.get(k)
    return default if v is None else v


def post_or_pre(r, k):
    v = r.get(k + "_post")
    if v is None:
        v = r.get(k + "_pre")
    return v


print("code   name       | 3post  49  54  53  SCRpre | cl=3p-49-54-ovf15 | 47pre 47post 48 | 47post-cl | 47pre-cl")
for code in sorted(rows):
    r = rows[code]
    t3 = post_or_pre(r, "i3")
    z = g(r, "i49_pre")
    l54 = g(r, "i54_pre")
    l53 = g(r, "i53_pre")
    scr = g(r, "i14_pre")
    ovf = max(0.0, l53 - 0.15 * scr)
    cl = (t3 or 0.0) - z - l54 - ovf
    e47pre = r.get("i47_pre")
    e47post = r.get("i47_post")
    e48 = post_or_pre(r, "i48")
    def fmt(x):
        return "." if x is None else ("%.1f" % x)
    d_post = None if e47post is None else e47post - cl
    d_pre = None if e47pre is None else e47pre - cl
    print("%s %-8s | %s %s %s %s %s | %s | %s %s %s | %s | %s" % (
        code, r["name"][:6], fmt(t3), fmt(z), fmt(l54), fmt(l53), fmt(scr), fmt(cl),
        fmt(e47pre), fmt(e47post), fmt(e48), fmt(d_post), fmt(d_pre)))
