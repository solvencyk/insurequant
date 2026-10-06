# -*- coding: utf-8 -*-
"""FINAL deletion set for item13 값_적용후 (parser/kics, 2026-09-20).

Settles validation's 56 vs orchestrator's 59.

Algebra (all from the master, no probe-JSON dependency):
    implied13 = item4_pre - item12_pre - item2_post          # true item13_post under H
    resid_pre = item4_pre - item12_pre - item13_pre - item2_pre
    over_by   = item13_pre - implied13 = Dtier - resid_pre,  Dtier = item2_post - item2_pre

So `over_by` mixes TWO things: the TFI tier movement (Dtier, the contamination we want)
and the 적용전 bridge's own pre-existing residual (resid_pre, NOT contamination — it is
equally present in the 적용전 column and deleting the post cell fixes nothing).

Sweeping `over_by` alone (orchestrator, 59) picks up 4 cells whose Dtier == 0 exactly:
their entire over_by is -resid_pre. Gating on Dtier (the delta-of-residual form) gives
the contamination-only set.

Criterion for DELETE:
    item13 값_적용후 present AND == 값            (it is a mirror)
    AND item4_pre, item12_pre, item2_pre, item2_post all present   (back-computable)
    AND |Dtier| > TOL                              (the TFI actually moved the tier split)
    AND over_by > TOL                              (the mirror really is too high)

Read-only. Writes the deletion list to data/_derived/.
"""
import json, io, os, sys
from collections import Counter, OrderedDict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + os.sep
MASTER = os.path.join(ROOT, "kics_disclosure.json")
V4 = os.path.join(ROOT, "data", "_derived", "_probe_20260919_mirror_audit_v4.json")
OUT = os.path.join(ROOT, "data", "_derived", "_probe_20260920_item13_final_set.json")

CODE, NAME, ITEM, PER, VAL, POST = "원보험사코드", "원수사명", "항목번호", "공시분기", "값", "값_적용후"
TOL = 2.0


def num(s):
    if s is None:
        return None
    t = str(s).strip().replace(",", "").replace("△", "-")
    if t in ("", "-", "N/A", "None"):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def main():
    with io.open(MASTER, "r", encoding="utf-8") as f:
        recs = json.load(f)
    cell, names = {}, {}
    for r in recs:
        cell[(r[CODE], r[PER], int(r[ITEM]))] = (r.get(VAL), r.get(POST))
        names[r[CODE]] = r.get(NAME)

    def g(c, q, it, col):
        t = cell.get((c, q, it))
        return None if not t else num(t[0] if col == "pre" else t[1])

    v4 = {}
    with io.open(V4, "r", encoding="utf-8") as f:
        for r in json.load(f)["rows"]:
            v4[(r["code"], r["q"])] = r["verdict"]

    delete, keep, tal = [], [], Counter()
    for (c, q, it), (v, p) in sorted(cell.items()):
        if it != 13 or p is None or str(p).strip() == "":
            continue
        pre13, post13 = num(v), num(p)
        if pre13 is None or post13 is None or abs(pre13 - post13) > 1e-9:
            tal["skip_not_a_mirror"] += 1
            continue
        tal["mirrored"] += 1
        i4p, i12p = g(c, q, 4, "pre"), g(c, q, 12, "pre")
        i2pre, i2post = g(c, q, 2, "pre"), g(c, q, 2, "post")
        if None in (i4p, i12p, i2pre, i2post):
            tal["skip_not_backcomputable"] += 1
            keep.append(OrderedDict([("code", c), ("name", names.get(c)), ("q", q),
                                     ("why_keep", "NOT_BACKCOMPUTABLE"),
                                     ("v4", v4.get((c, q))), ("item13", pre13)]))
            continue
        implied = i4p - i12p - i2post
        over = pre13 - implied
        dtier = i2post - i2pre
        resid_pre = i4p - i12p - pre13 - i2pre
        rec = OrderedDict([
            ("code", c), ("name", names.get(c)), ("q", q), ("v4", v4.get((c, q))),
            ("item13_mirrored", pre13), ("item13_true_implied", round(implied, 2)),
            ("over_by", round(over, 2)), ("Dtier_item2_post_minus_pre", round(dtier, 2)),
            ("resid_pre", round(resid_pre, 2)),
            ("item2_pre", i2pre), ("item2_post", i2post),
            ("item3_pre", g(c, q, 3, "pre")), ("item3_post", g(c, q, 3, "post")),
            ("item4_pre", i4p), ("item12_pre", i12p),
        ])
        if abs(dtier) > TOL and over > TOL:
            tal["DELETE"] += 1
            tal["DELETE__v4_" + str(v4.get((c, q)))] += 1
            delete.append(rec)
        else:
            why = ("TIER_DID_NOT_MOVE(over_by is pre-column resid)" if abs(dtier) <= TOL and over > TOL
                   else ("TIER_MOVED_BUT_MIRROR_MATCHES" if abs(dtier) > TOL else "NO_MOVE_NO_OVER"))
            rec["why_keep"] = why
            tal["KEEP__" + why.split("(")[0]] += 1
            keep.append(rec)

    payload = {"tol": TOL, "tally": dict(sorted(tal.items())),
               "delete_count": len(delete),
               "delete_by_company": dict(Counter("%s %s" % (r["code"], r["name"]) for r in delete)),
               "delete": delete,
               "keep_flagged": [r for r in keep if r.get("why_keep") != "NO_MOVE_NO_OVER"]}
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("tally:", json.dumps(payload["tally"], ensure_ascii=False))
    print("DELETE count =", len(delete))
    print("by company:", json.dumps(payload["delete_by_company"], ensure_ascii=False))
    print("\n-- kept despite over_by>tol (tier never moved) --")
    for r in payload["keep_flagged"]:
        if r.get("why_keep", "").startswith("TIER_DID_NOT_MOVE"):
            print("   %s %s %s over_by=%s Dtier=%s resid_pre=%s v4=%s"
                  % (r["code"], r["name"], r["q"], r["over_by"], r["Dtier_item2_post_minus_pre"],
                     r["resid_pre"], r["v4"]))
    print("\n-- tier moved but mirror matches (masked) --")
    for r in payload["keep_flagged"]:
        if r.get("why_keep") == "TIER_MOVED_BUT_MIRROR_MATCHES":
            print("   %s %s %s over_by=%s Dtier=%s resid_pre=%s v4=%s"
                  % (r["code"], r["name"], r["q"], r["over_by"], r["Dtier_item2_post_minus_pre"],
                     r["resid_pre"], r["v4"]))
    print("\n->", OUT)


if __name__ == "__main__":
    main()
