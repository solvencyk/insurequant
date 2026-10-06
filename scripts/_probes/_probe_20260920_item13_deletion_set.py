# -*- coding: utf-8 -*-
"""2026-09-20 parser(kics): settle the item13 post-mirror deletion set (56 vs 59).

validation counted 56 (55 machine-confirmed + 메리츠화재 2026.2Q, masked by that
bucket's stale item2/3 post) by iterating ONLY the CONTAMINATED buckets of
_probe_20260919_mirror_audit_v4.json, tol 2.0.
orchestrator counted 59 by sweeping EVERY back-computable mirrored item13 cell
(240 of them), tol 1.5.

This probe recomputes from the master with no bucket pre-filter, then labels each
over-cell with the v4 bucket verdict so the two lists can be diffed cell by cell.

    implied13(true item13_post) = item4_pre - item12_pre - item2_post

Read-only. Writes one JSON under data/_derived/.
"""
import json, io, os, sys
from collections import Counter, OrderedDict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + os.sep
MASTER = os.path.join(ROOT, "kics_disclosure.json")
V4 = os.path.join(ROOT, "data", "_derived", "_probe_20260919_mirror_audit_v4.json")
OUT = os.path.join(ROOT, "data", "_derived", "_probe_20260920_item13_deletion_set.json")

CODE, NAME, ITEM, PER, VAL, POST = "원보험사코드", "원수사명", "항목번호", "공시분기", "값", "값_적용후"
FLIP = {("KR1000", "2023.4Q"), ("KR1000", "2024.2Q")}


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
        M = json.load(f)
    recs = M["records"] if isinstance(M, dict) and "records" in M else M

    cell, names = {}, {}
    for r in recs:
        cell[(r[CODE], r[PER], int(r[ITEM]))] = (r.get(VAL), r.get(POST))
        names[r[CODE]] = r.get(NAME)

    def g(c, q, it, col):
        t = cell.get((c, q, it))
        return None if not t else num(t[0] if col == "pre" else t[1])

    # v4 bucket verdicts
    v4 = {}
    with io.open(V4, "r", encoding="utf-8") as f:
        for r in json.load(f)["rows"]:
            v4[(r["code"], r["q"])] = r["verdict"]

    rows, tal = [], Counter()
    for (c, q, it), (v, p) in sorted(cell.items()):
        if it != 13 or p is None or str(p).strip() == "":
            continue
        tal["item13_post_present"] += 1
        pre13, post13 = num(v), num(p)
        mirrored = (post13 is not None and pre13 is not None and abs(post13 - pre13) < 1e-9)
        if not mirrored:
            tal["item13_post_NOT_mirrored"] += 1
            continue
        tal["item13_mirrored"] += 1
        i4p, i12p, i2post = g(c, q, 4, "pre"), g(c, q, 12, "pre"), g(c, q, 2, "post")
        if None in (i4p, i12p, i2post):
            tal["not_backcomputable"] += 1
            rows.append(OrderedDict([("code", c), ("name", names.get(c)), ("q", q),
                                     ("v4_verdict", v4.get((c, q))), ("cls", "NOT_BACKCOMPUTABLE"),
                                     ("item13_pre", pre13), ("implied13", None), ("over_by", None),
                                     ("item4_pre", i4p), ("item12_pre", i12p), ("item2_post", i2post)]))
            continue
        implied = i4p - i12p - i2post
        over = pre13 - implied
        # classify at both tolerances in play
        cls15 = "OVER" if over > 1.5 else ("UNDER" if over < -1.5 else "EQ")
        cls20 = "OVER" if over > 2.0 else ("UNDER" if over < -2.0 else "EQ")
        tal["tol1.5_" + cls15] += 1
        tal["tol2.0_" + cls20] += 1
        vd = v4.get((c, q))
        grp = "BASELINE_FLIP" if (c, q) in FLIP else (vd or "NO_V4_ROW")
        if cls20 == "OVER":
            tal["tol2.0_OVER__" + grp] += 1
        if cls15 == "OVER":
            tal["tol1.5_OVER__" + grp] += 1
        rows.append(OrderedDict([
            ("code", c), ("name", names.get(c)), ("q", q),
            ("v4_verdict", vd), ("group", grp),
            ("cls_tol1_5", cls15), ("cls_tol2_0", cls20),
            ("item13_pre_eq_post", pre13), ("implied13", round(implied, 2)),
            ("over_by", round(over, 2)),
            ("item3_pre", g(c, q, 3, "pre")), ("item3_post", g(c, q, 3, "post")),
            ("item2_pre", g(c, q, 2, "pre")), ("item2_post", i2post),
            ("item4_pre", i4p), ("item4_post", g(c, q, 4, "post")),
            ("item12_pre", i12p), ("item12_post", g(c, q, 12, "post")),
        ]))

    over20 = [r for r in rows if r.get("cls_tol2_0") == "OVER"]
    over15 = [r for r in rows if r.get("cls_tol1_5") == "OVER"]
    under15 = [r for r in rows if r.get("cls_tol1_5") == "UNDER"]

    payload = {
        "tally": dict(sorted(tal.items())),
        "counts": {
            "item13_mirrored_total": tal["item13_mirrored"],
            "backcomputable": tal["item13_mirrored"] - tal["not_backcomputable"],
            "over_tol2.0": len(over20),
            "over_tol1.5": len(over15),
            "under_tol1.5": len(under15),
        },
        "over_tol1_5_by_group": dict(Counter(r["group"] for r in over15)),
        "over_tol2_0_by_group": dict(Counter(r["group"] for r in over20)),
        "delta_1_5_minus_2_0": [ [r["code"], r["name"], r["q"], r["over_by"], r["group"]]
                                 for r in over15 if r["cls_tol2_0"] != "OVER" ],
        "rows": rows,
    }
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("counts :", json.dumps(payload["counts"], ensure_ascii=False))
    print("over1.5 by group:", json.dumps(payload["over_tol1_5_by_group"], ensure_ascii=False))
    print("over2.0 by group:", json.dumps(payload["over_tol2_0_by_group"], ensure_ascii=False))
    print("delta(1.5 not 2.0):", json.dumps(payload["delta_1_5_minus_2_0"], ensure_ascii=False))
    print("tally  :", json.dumps(payload["tally"], ensure_ascii=False))
    print("->", OUT)


if __name__ == "__main__":
    main()
