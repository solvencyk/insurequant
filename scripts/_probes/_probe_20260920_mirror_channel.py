# -*- coding: utf-8 -*-
"""2026-09-20 validation re-audit: WHICH of the mirrored items (4/12/13) is wrong?

Context. The 2026-09-19 audit found 60 buckets where item4/12/13 `값_적용후` was
mirrored from `값` although the common TFI actually moved the tier split, and called
all 176 mirrored cells in those buckets contaminated (170 after excluding the two
코리안리 baseline-flip buckets). That over-counts.

The common TFI (제도시행 前 기발행 자본증권의 가용자본 인정범위 확대) reclassifies
capital securities between tiers. It does not change Ⅰ(순자산) or Ⅱ(불인정항목); it
changes Ⅲ(보완자본 재분류). So under hypothesis H only item13's mirror is wrong and
item4/item12's mirrors are right.

Test. item2_post is issuer-disclosed (parsed by the golden extractor from the 공통적용
2-column table). Under H:
    implied13 = item4_pre - item12_pre - item2_post          (the true item13_post)
Two independent references:
  (R1) assumption-free, available where item13_pre == item3_pre (all 보완자본 comes from
       reclassification, so item13_post must equal the disclosed item3_post):
           implied13 == item3_post
  (R2) weaker, available everywhere: the non-reclassification part of 보완자본 is
       TFI-invariant:
           (item3_post - implied13) == (item3_pre - item13_pre)

Read-only: reads kics_disclosure.json and the prior probe; writes one file under
data/_derived/. Touches no master.
"""
import json, io, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + os.sep
MASTER = os.path.join(ROOT, "kics_disclosure.json")
PRIOR = os.path.join(ROOT, "data", "_derived", "_probe_20260919_mirror_audit_v4.json")
OUT = os.path.join(ROOT, "data", "_derived", "_probe_20260920_mirror_channel.json")

CODE, NAME, ITEM, PER, VAL, POST = "원보험사코드", "원수사명", "항목번호", "공시분기", "값", "값_적용후"
TOL = 2.0
FLIP = {("KR1000", "2023.4Q"), ("KR1000", "2024.2Q")}   # baseline-flip buckets, see A-4b


def num(s):
    if s is None:
        return None
    t = str(s).strip().replace(",", "").replace("\u25b3", "-")
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

    # ---- census of mirrored 4/12/13 cells (independent recount) ----------
    cells = buckets = comps = 0
    bset, cset = set(), set()
    per_item, eq = Counter(), 0
    for (c, q, it), (v, p) in cell.items():
        if it not in (4, 12, 13) or p is None or str(p).strip() == "":
            continue
        cells += 1
        per_item[it] += 1
        bset.add((c, q))
        cset.add(c)
        if str(p).strip() == str(v).strip():
            eq += 1
    census = {"cells": cells, "buckets": len(bset), "companies": len(cset),
              "per_item": dict(sorted(per_item.items())), "post_equals_pre": eq}

    with io.open(PRIOR, "r", encoding="utf-8") as f:
        contam = [r for r in json.load(f)["rows"] if r["verdict"] == "CONTAMINATED"]

    tal, rows = Counter(), []
    for r in contam:
        c, q = r["code"], r["q"]
        grp = "BASELINE_FLIP" if (c, q) in FLIP else "CONTAM"
        i4p, i12p, i13p, i3p = g(c, q, 4, "pre"), g(c, q, 12, "pre"), g(c, q, 13, "pre"), g(c, q, 3, "pre")
        i2post, i3post = g(c, q, 2, "post"), g(c, q, 3, "post")
        mirrored = [it for it in (4, 12, 13) if g(c, q, it, "post") is not None]
        for it in mirrored:
            tal["%s_mirrored_item%d" % (grp, it)] += 1
        if None in (i4p, i12p, i2post):
            tal[grp + "_untestable"] += 1
            continue
        implied13 = i4p - i12p - i2post
        r1 = None
        if i13p is not None and i3p is not None and i3post is not None and abs(i13p - i3p) <= 1.0:
            r1 = implied13 - i3post
            tal["R1_" + ("holds" if abs(r1) <= TOL else "FAILS")] += 1
        r2 = None
        if None not in (i3post, i3p, i13p):
            r2 = (i3post - implied13) - (i3p - i13p)
            tal["R2_" + ("holds" if abs(r2) <= TOL else "FAILS")] += 1
        wrong13 = 13 in mirrored and i13p is not None and abs(i13p - implied13) > TOL
        if wrong13:
            tal[grp + "_item13_WRONG"] += 1
        rows.append({
            "code": c, "name": names.get(c), "q": q, "group": grp,
            "mirrored_items": mirrored,
            "item13_mirrored": i13p, "item13_true_implied": round(implied13, 2),
            "over_by": None if i13p is None else round(i13p - implied13, 2),
            "R1_gap_vs_item3_post": None if r1 is None else round(r1, 2),
            "R2_resid_other": None if r2 is None else round(r2, 2),
            "item13_mirror_wrong": wrong13,
            "item4_item12_mirror_corroborated": (r2 is not None and abs(r2) <= TOL),
        })

    payload = {
        "census_mirrored_4_12_13": census,
        "contaminated_buckets_from_prior_probe": len(contam),
        "tally": dict(sorted(tal.items())),
        "verdict": {
            "cells_actually_wrong_item13_only": sum(1 for r in rows
                                                    if r["group"] == "CONTAM" and r["item13_mirror_wrong"]),
            "cells_corroborated_correct_item4_item12": (tal["CONTAM_mirrored_item4"]
                                                        + tal["CONTAM_mirrored_item12"]),
        },
        "rows": rows,
    }
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("census:", json.dumps(census, ensure_ascii=False))
    print("tally :", json.dumps(payload["tally"], ensure_ascii=False))
    print("verdict:", json.dumps(payload["verdict"], ensure_ascii=False))
    print("->", OUT)


if __name__ == "__main__":
    main()
