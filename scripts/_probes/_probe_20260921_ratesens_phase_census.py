"""kics_rate_sensitivity.json — phase-level (적용전/적용후) completeness census, ALL quarters.

Read-only. Answers inbox/validation/20260921T0100Z (parser: RS1-5 never census the phase level).

Expected grid per (company, quarter) in the kics_disclosure cohort (REGIME_START+, even quarters):
  2 phases x 3 measures (지급여력비율 / 지급여력금액 / 지급여력기준금액) = 6 rows,
  each row 5 shock columns non-null.

Also measures two neighbours the ticket did not ask about but the same blind spot implies:
  * RS2 anchors only the 적용전 base to kics_disclosure item1/14/27 — the 적용후 base is never
    anchored to 값_적용후. Measured here as "RS2_POST" so a wrong 적용전->적용후 mirror is visible.
  * orphans: rate-sensitivity rows whose (code, quarter) is not in the kics_disclosure cohort.

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/_probe_20260921_ratesens_phase_census.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from validate_kics_rate_sensitivity import REGIME_START, SHOCK_COLS  # noqa: E402

MEASURES = ("지급여력비율", "지급여력금액", "지급여력기준금액")
PHASES = ("적용전", "적용후")
OUT = ROOT / "data" / "_derived" / "_probe_20260921_ratesens_phase_census.json"


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main() -> int:
    rs = json.loads((ROOT / "kics_rate_sensitivity.json").read_text(encoding="utf-8"))
    kd = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

    cohort: dict[tuple[str, str], str] = {}
    head: dict[tuple[str, str], dict] = defaultdict(dict)   # (code,q) -> {item: (pre, post)}
    for r in kd:
        cq = (r["원보험사코드"], r["공시분기"])
        cohort[cq] = r["원수사명"]
        n = r.get("항목번호")
        if n in (1, 14, 27):
            head[cq][n] = (_f(r.get("값")), _f(r.get("값_적용후")))

    g: dict[tuple[str, str, str], dict[str, dict]] = defaultdict(dict)
    for r in rs:
        g[(r["원보험사코드"], r["공시분기"], r["경과조치여부"])][r["measure구분"]] = r
    rs_cq = {(k[0], k[1]) for k in g}

    regime = sorted({q for (_, q) in cohort if q >= REGIME_START and q.endswith(("2Q", "4Q"))})
    print(f"regime quarters (even, >= {REGIME_START}): {regime}")
    print(f"cohort buckets in regime: {sum(1 for (c, q) in cohort if q in regime)}   rs buckets: {len(rs_cq)}")

    holes = []          # phase-level: a measure row missing
    null_cells = []     # a present row with a null shock cell
    rs5_absent = []     # whole bucket absent (RS5 territory, counted for context)
    per_cq = []
    for (code, q), name in sorted(cohort.items()):
        if q not in regime:
            continue
        if (code, q) not in rs_cq:
            rs5_absent.append((code, name, q))
            continue
        rec = {"code": code, "name": name, "quarter": q, "missing": {}, "null_cells": {}}
        for ph in PHASES:
            m = g.get((code, q, ph), {})
            miss = [x for x in MEASURES if x not in m]
            if miss:
                rec["missing"][ph] = miss
                for x in miss:
                    holes.append((code, name, q, ph, x))
            for x, row in m.items():
                nulls = [c for c in SHOCK_COLS if row.get(c) is None]
                if nulls:
                    rec["null_cells"][f"{ph}/{x}"] = nulls
                    null_cells.append((code, name, q, ph, x, nulls))
        per_cq.append(rec)

    print(f"\n[RS5 territory] whole bucket absent: {len(rs5_absent)}")
    print(f"[RS6] phase-level missing measure rows: {len(holes)}")
    by_bucket = Counter((h[0], h[2]) for h in holes)
    for (code, q), n in sorted(by_bucket.items()):
        ph = sorted({h[3] for h in holes if (h[0], h[2]) == (code, q)})
        nm = cohort[(code, q)]
        print(f"   {code} {nm:14s} {q}  missing rows={n}  phases={ph}")
    by_phase = Counter(h[3] for h in holes)
    print(f"   by phase: {dict(by_phase)}")
    pat = Counter()
    for (code, q) in by_bucket:
        pre = any(h[3] == "적용전" for h in holes if (h[0], h[2]) == (code, q))
        post = any(h[3] == "적용후" for h in holes if (h[0], h[2]) == (code, q))
        pat["적용전만 결측" if pre and not post else "적용후만 결측" if post and not pre else "양쪽 결측"] += 1
    print(f"   pattern: {dict(pat)}")
    print(f"[RS6] null shock cells inside present rows: {len(null_cells)}")
    for code, name, q, ph, x, nulls in null_cells[:30]:
        print(f"   {code} {name:14s} {q} {ph}/{x}: {nulls}")

    # ---- RS2_POST: 적용후 base vs 값_적용후 (item1 / item14 / item27) ----
    CHK = [("지급여력금액", 1, 2.0), ("지급여력기준금액", 14, 2.0), ("지급여력비율", 27, 0.5)]
    rs2_post_fail, rs2_post_checked, rs2_post_skipped = [], 0, Counter()
    for (code, q, ph), m in g.items():
        if ph != "적용후":
            continue
        h = head.get((code, q), {})
        for meas, item, tol in CHK:
            row = m.get(meas)
            if not row:
                rs2_post_skipped["row_missing"] += 1
                continue
            bv = _f(row.get("base"))
            pv = (h.get(item) or (None, None))[1]
            if bv is None or pv is None:
                rs2_post_skipped["headline_post_missing" if pv is None else "base_null"] += 1
                continue
            rs2_post_checked += 1
            if abs(bv - pv) > tol:
                rs2_post_fail.append((code, cohort.get((code, q), "?"), q, meas, bv, pv, round(bv - pv, 2)))
    print(f"\n[RS2_POST] 적용후 base vs 값_적용후: checked={rs2_post_checked} fail={len(rs2_post_fail)} skipped={dict(rs2_post_skipped)}")
    for rec in rs2_post_fail:
        print(f"   {rec[0]} {rec[1]:14s} {rec[2]} {rec[3]}: base_post={rec[4]} vs headline_post={rec[5]} (d={rec[6]:+})")

    # ---- mirror consistency: rows 적용전==적용후 while headline pre!=post ----
    mirror_bad = []
    for (code, q, ph), m in g.items():
        if ph != "적용전":
            continue
        mp = g.get((code, q, "적용후"), {})
        if not mp:
            continue
        same = all(
            x in m and x in mp and all(m[x].get(c) == mp[x].get(c) for c in SHOCK_COLS)
            for x in MEASURES
        )
        if not same:
            continue
        h = head.get((code, q), {})
        diffs = {it: (pre, post) for it, (pre, post) in h.items()
                 if pre is not None and post is not None and abs(pre - post) > (0.5 if it == 27 else 2.0)}
        if diffs:
            mirror_bad.append((code, cohort.get((code, q), "?"), q, diffs))
    print(f"\n[MIRROR vs HEADLINE] rows 전==후 but headline 전!=후: {len(mirror_bad)}")
    for code, name, q, diffs in mirror_bad:
        print(f"   {code} {name:14s} {q} {diffs}")

    orphans = sorted(rs_cq - set(cohort))
    print(f"\n[orphans] rs (code,quarter) not in kics_disclosure cohort: {len(orphans)} {orphans[:10]}")

    OUT.write_text(json.dumps({
        "regime_quarters": regime,
        "rs5_whole_bucket_absent": rs5_absent,
        "rs6_missing_rows": holes,
        "rs6_missing_by_bucket": {f"{c}|{q}": n for (c, q), n in by_bucket.items()},
        "rs6_pattern": dict(pat),
        "rs6_null_cells": null_cells,
        "rs2_post": {"checked": rs2_post_checked, "fail": rs2_post_fail, "skipped": dict(rs2_post_skipped)},
        "mirror_vs_headline_bad": [(c, n, q, {str(k): v for k, v in d.items()}) for c, n, q, d in mirror_bad],
        "orphans": orphans,
        "per_bucket": per_cq,
    }, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
