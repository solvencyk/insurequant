"""s2b_conflict_blocks.py -- step 2b (READ-ONLY).  Normalise the core cross-filing comparison and build one overlay PLAN per conflicting block.

Normalisations (each is recorded on the block so nothing is silently dropped):
  * unit scale   : when >=3 comparable items all show latest/master ~ 100 (or ~0.01) the filing prints 백만원 where the master holds 억원
                   (or the reverse); latest is rescaled and the block is flagged SCALE_FIXED
  * item 22      : master stores the positive magnitude (parentheses in the filing) -> compare |latest|
  * rounding     : the project's detect_kics_restatement.differs() (coarser printed decimals) decides what counts as a difference
Control column : the same extractor read on the quarter's OWN filing (cur column).  If the own-filing print deviates from the master on the
                 same items as the latest print does, the deviation is an extraction/layout artefact (EXTRACTION_SUSPECT), not a restatement.

Output: conflict_blocks.json (all blocks with their status) and plans/<code>_<quarter>.json for every block that has an actionable core diff.
"""
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402

utf8_stdout()
import detect_kics_restatement as det  # noqa: E402
import validate_kics_disclosure as vkd  # noqa: E402

APPLIERS = set(vkd._TRANSITION_APPLIERS)
rows = read_rows()
midx, names = master_index(rows)
codes = sorted(names)
PLANS = OUT / "plans"
PLANS.mkdir(parents=True, exist_ok=True)


def load(period, code):
    f = CACHE / f"core_{period}_{code}.json"
    return read_json(f) if f.exists() else None


def col(rec, c):
    if not rec or rec["status"] not in ("OK", "VISION_ONLY"):
        return None
    d = rec["cols"].get(c)
    if not d:
        return None
    return {int(k): (v[0], v[1]) for k, v in d.items() if v[0] is not None}


def mdec(v):
    return 2 if abs(v - round(v)) > 1e-9 else 0


def src_of(rec, c=None):
    if not rec or not rec.get("pdf"):
        return None
    return rec["pdf"] + " p" + "+".join(str(x) for x in (rec.get("pages") or []))


def fmt_like(old, new):
    """Write `new` in the same style the master already uses for that cell."""
    if isinstance(old, str) or old is None:
        if abs(new - round(new)) < 1e-9:
            return str(int(round(new)))
        return f"{new:.2f}".rstrip("0").rstrip(".")
    if isinstance(old, int) and abs(new - round(new)) < 1e-9:
        return int(round(new))
    return float(new)


def detect_scale(pairs):
    """pairs = [(master, latest)] -> 1.0 | 100.0 (latest must be divided by 100) | 0.01 (latest must be multiplied)"""
    ratios = [l / m for m, l in pairs if m and abs(m) >= 1 and l not in (None, 0)]
    if len(ratios) >= 3:
        n = len(ratios)
        if sum(1 for r in ratios if 98.5 <= r <= 101.5) >= max(3, int(0.6 * n)):
            return 100.0
        if sum(1 for r in ratios if 0.0098 <= r <= 0.0102) >= max(3, int(0.6 * n)):
            return 0.01
    return 1.0


out_blocks = []
for code in codes:
    for q in QUARTERS[:-1]:
        if (code, q) not in midx:
            continue
        q1, q2 = qadd(q, 1), qadd(q, 2)
        rec_own = load(period_of(q), code)
        rec1 = load(period_of(q1), code) if q1 else None
        rec2 = load(period_of(q2), code) if q2 else None
        own, l1, l2 = col(rec_own, "cur"), col(rec1, "prev"), col(rec2, "prev2")
        if q2 and l2 is not None:
            latest, label, lrec = l2, f"F({q2}) 전전분기 열", rec2
        elif l1 is not None:
            latest, label, lrec = l1, f"F({q1}) 직전분기 열", rec1
        else:
            latest, label, lrec = None, None, None
        m = midx[(code, q)]
        blk = {"code": code, "name": names[code], "quarter": q, "applier": code in APPLIERS,
               "even": is_even(q), "own_status": rec_own["status"] if rec_own else "NO_REC",
               "q1_status": (rec1["status"] if rec1 else ("NA" if not q1 else "NO_REC")),
               "q2_status": (rec2["status"] if rec2 else ("NA" if not q2 else "NO_REC")),
               "latest_label": label, "latest_src": src_of(lrec), "own_src": src_of(rec_own),
               "status": None, "flags": [], "diffs": [], "own_dev": [], "l1_vs_l2": [], "scale": 1.0, "compared": 0}
        if latest is None:
            blk["status"] = "UNCOVERED"
            out_blocks.append(blk)
            continue
        # unit scale
        pairs = []
        for it in range(1, 27):
            mv = num(m[it][0]) if it in m else None
            if mv is not None and it in latest:
                pairs.append((mv, latest[it][0]))
        sc = detect_scale(pairs)
        blk["scale"] = sc
        if sc != 1.0:
            blk["flags"].append("SCALE_FIXED(x%g)" % (1.0 / sc))
        for it in range(1, 27):
            mv = num(m[it][0]) if it in m else None
            if it not in latest:
                continue
            lv, ld = latest[it]
            lv = lv / sc if sc != 1.0 else lv
            if it == 22:
                lv = abs(lv)
            if mv is None:
                continue
            blk["compared"] += 1
            dd, bad = det.differs((lv, 2 if sc != 1.0 else ld), (mv, mdec(mv)))
            if bad:
                blk["diffs"].append({"item": it, "master": mv, "latest": round(lv, 4), "delta": round(lv - mv, 4)})
        # control column (own filing)
        if own:
            own_pairs = [(num(m[it][0]), own[it][0]) for it in range(1, 27) if it in m and it in own and num(m[it][0]) is not None]
            sc_own = detect_scale(own_pairs)
            for it in range(1, 27):
                mv = num(m[it][0]) if it in m else None
                if it not in own or mv is None:
                    continue
                ov, od = own[it]
                if sc_own != 1.0:
                    ov = ov / sc_own
                    od = 2
                if it == 22:
                    ov = abs(ov)
                dd, bad = det.differs((ov, od), (mv, mdec(mv)))
                if bad:
                    blk["own_dev"].append({"item": it, "master": mv, "own": ov})
        if l1 is not None and l2 is not None:
            for it in range(1, 27):
                if it in l1 and it in l2:
                    dd, bad = det.differs(l1[it], l2[it])
                    if bad:
                        blk["l1_vs_l2"].append({"item": it, "l1": l1[it][0], "l2": l2[it][0]})
        # dash-or-blank in a mapped row of the latest column while the master holds a non-zero value (information only, never overlaid)
        raw_latest = (lrec or {}).get("cols", {}).get("prev2" if label and "전전분기" in label else "prev", {}) if lrec else {}
        dash_items = []
        for it in range(1, 27):
            v = raw_latest.get(str(it))
            if v is not None and v[0] is None and it in m and num(m[it][0]) is not None and abs(num(m[it][0])) >= 0.5:
                dash_items.append(it)
        if dash_items:
            blk["flags"].append("LATEST_DASH_OR_BLANK_VS_MASTER_NONZERO(items %s)" % dash_items)
        gf_items = set((lrec or {}).get("gapfill_items") or [])
        gf_hit = sorted(gf_items & {d["item"] for d in blk["diffs"]})
        if gf_hit:
            blk["flags"].append("GAPFILL_ROW_IN_DIFF(items %s: row assigned by form order, not by label)" % gf_hit)
        if not blk["diffs"]:
            blk["status"] = "CLEAN"
        else:
            diff_items = {d["item"] for d in blk["diffs"]}
            own_items = {d["item"] for d in blk["own_dev"]}
            # artefact suspicion: the own-filing control deviates from master on (nearly) the same items
            if own and len(own_items & diff_items) >= max(2, int(0.6 * len(diff_items))):
                blk["flags"].append("EXTRACTION_SUSPECT(own-filing control deviates the same way)")
            if own is None:
                blk["flags"].append("NO_OWN_CONTROL(%s)" % blk["own_status"])
            if blk["l1_vs_l2"]:
                blk["flags"].append("LATER_PRINTINGS_DIFFER(F+1 vs F+2)")
            mx = max(abs(d["delta"]) for d in blk["diffs"])
            blk["max_abs_delta"] = mx
            blk["tier"] = "ROUND1" if mx <= 1.0 + 1e-9 else ("SMALL" if mx <= 10 else "MATERIAL")
            blk["status"] = "CONFLICT"
        out_blocks.append(blk)

        # ---------------- overlay plan for conflicting blocks
        if blk["status"] == "CONFLICT":
            edits, post_indep, mirror = [], [], []
            for d in blk["diffs"]:
                it = d["item"]
                old_pre, old_post, _ri = m[it]
                new_val = d["latest"]
                edits.append({"code": code, "q": q, "item": it, "field": "값", "old": old_pre, "new": fmt_like(old_pre, new_val),
                              "src": blk["latest_src"], "col": label})
                if old_post is not None and old_post != "":
                    if abs(num(old_post) - num(old_pre)) < 1e-9:
                        edits.append({"code": code, "q": q, "item": it, "field": "값_적용후", "old": old_post, "new": fmt_like(old_post, new_val),
                                      "src": blk["latest_src"], "col": label + " (mirror)"})
                        mirror.append(it)
                    else:
                        post_indep.append(it)
            blk["post_mirrored_items"] = mirror
            blk["post_independent_items"] = post_indep
            if post_indep:
                blk["flags"].append("POST_COLUMN_NOT_REPLACEABLE(items %s)" % post_indep)
            plan = {"name": f"{code}_{q}", "code": code, "quarter": q, "edits": edits, "inserts": [],
                    "latest_label": label, "latest_src": blk["latest_src"], "flags": blk["flags"]}
            write_json_lf(PLANS / f"{code}_{q}.json", plan)

write_json_lf(OUT / "conflict_blocks.json", out_blocks)
c = Counter(b["status"] for b in out_blocks)
print("blocks:", len(out_blocks), dict(c))
print("CONFLICT by tier:", dict(Counter(b.get("tier") for b in out_blocks if b["status"] == "CONFLICT")))
print("CONFLICT with EXTRACTION_SUSPECT:", sum(1 for b in out_blocks if b["status"] == "CONFLICT" and any(f.startswith("EXTRACTION_SUSPECT") for f in b["flags"])))
print("CONFLICT with SCALE_FIXED:", [(b["code"], b["quarter"]) for b in out_blocks if any(f.startswith("SCALE_FIXED") for f in b["flags"])][:40])
for b in out_blocks:
    if b["status"] == "CONFLICT":
        print(f"  {b['code']} {b['name'][:9]:9s} {b['quarter']} {b.get('tier'):8s} n={len(b['diffs']):2d} {[ (d['item'], d['master'], d['latest']) for d in b['diffs']][:6]} {b['flags']}")
