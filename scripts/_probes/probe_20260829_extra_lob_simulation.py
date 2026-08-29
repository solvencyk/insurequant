"""Full-bucket simulation: add the extra-LOB slot (항목번호 "2-N") to the
보험손익 leg-coverage / dual equation in `scripts/validate_master_tables.py`.

Claim under test (parser, commit 15a61d1, inbox/parser/20260829T1700Z__validation__
MULTI__pl_item1_leg_coverage.md §2): 코리안리재보험's item13(자동차) is legitimately
absent from the source, and the residual comes from the *validator's* equation
missing 코리안리's fourth LOB leg — item"2-1" 장기재보험 손익, which the builder
already publishes and already folds into its own Tier-2 RC gate
(`build_pl_breakdown.py` L249-252 `_extra_lob`).

This probe recomputes the 보험손익 verdict for EVERY (company, quarter) bucket
under both the current 3-leg equation and the proposed 3-leg + extra-LOB equation,
and reports every verdict change in both directions (closes / newly breaks).

Read-only.  Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260829_extra_lob_simulation.py
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PL_PATH = ROOT / "PL_breakdown.json"
DEFAULT_FLOOR = 200.0        # mirrors validate_master_tables.DEFAULT_FLOOR (L254)
LOB_KEYS = ("생명장기손익", "자동차손익", "일반손익")
EXTRA_LOB_NO = re.compile(r"^2-\d+$")


def norm(s: str) -> str:
    return (s or "").replace(" ", "")


def load() -> tuple[dict, dict]:
    rows = json.loads(PL_PATH.read_text(encoding="utf-8"))
    pl: dict = defaultdict(dict)
    extra: dict = defaultdict(list)          # (co,q) -> [(항목번호, 항목명, 값)]
    for r in rows:
        key = (r["원수사명"], r["공시분기"])
        pl[key][norm(r["항목명"])] = r["값"]
        no = r.get("항목번호")
        if isinstance(no, str) and EXTRA_LOB_NO.match(no):
            extra[key].append((no, r["항목명"], r["값"]))
    return pl, extra


def verdict(m: dict, extra_rows: list, use_extra: bool):
    """Returns (state, diff, zerofilled_legs).  state in PASS/FAIL/NOLHS."""
    bo = m.get("보험손익")
    if bo is None:
        return "NOLHS", None, []
    raw_lob = [m.get(k) for k in LOB_KEYS]
    zf = [k for k, v in zip(LOB_KEYS, raw_lob) if v is None]
    bare = sum(0.0 if v is None else v for v in raw_lob)
    if use_extra:
        bare += sum(v for _, _, v in extra_rows if v is not None)
    cands = [bare]
    oi, oe = m.get("기타영업수익"), m.get("기타사업비용")
    if oi is not None and oe is not None:
        cands.append(bare + oi - oe)
    diff = min((c - bo for c in cands), key=abs)
    state = "FAIL" if abs(diff) > max(0.001 * abs(bo), DEFAULT_FLOOR) else "PASS"
    return state, diff, zf


def main() -> None:
    pl, extra = load()
    tally = {"before": defaultdict(int), "after": defaultdict(int)}
    legcov = {"before": defaultdict(int), "after": defaultdict(int)}
    changed = []

    for (co, q), m in sorted(pl.items()):
        ex = extra.get((co, q), [])
        sb, db, zfb = verdict(m, ex, use_extra=False)
        sa, da, zfa = verdict(m, ex, use_extra=True)
        tally["before"][sb] += 1
        tally["after"][sa] += 1
        # leg-coverage sub-tally = buckets where at least one standard leg is missing
        if sb != "NOLHS" and zfb:
            legcov["before"][sb] += 1
        if sa != "NOLHS" and zfa:
            legcov["after"][sa] += 1
        if sb != sa or (ex and sb == "FAIL"):
            changed.append((co, q, sb, db, sa, da, zfb, ex))

    print("=" * 78)
    print("FULL-BUCKET SIMULATION  (buckets = %d)" % len(pl))
    print("=" * 78)
    for phase in ("before", "after"):
        t = tally[phase]
        print(f"  보험손익 전체   {phase:<6s} PASS={t['PASS']:>4d} FAIL={t['FAIL']:>3d} NOLHS={t['NOLHS']:>3d}")
    for phase in ("before", "after"):
        t = legcov[phase]
        print(f"  2e.leg-coverage {phase:<6s} 닫힘={t['PASS']:>4d} 깨짐={t['FAIL']:>3d}")

    print()
    print("-- verdict changes / extra-LOB-affected buckets --")
    if not changed:
        print("   (none)")
    for co, q, sb, db, sa, da, zfb, ex in changed:
        exs = ", ".join(f"{no}={v}" for no, _, v in ex) if ex else "-"
        dbs = f"{db:+.1f}" if db is not None else "n/a"
        das = f"{da:+.1f}" if da is not None else "n/a"
        mark = "CHANGED" if sb != sa else "same   "
        print(f"  {mark} {co:<14s} {q}  {sb}->{sa}  diff {dbs:>12s} -> {das:>10s}  "
              f"0fill={'+'.join(zfb) or '-'}  extra[{exs}]")

    # Which companies would newly break?
    newly_broken = [c for c in changed if c[2] == "PASS" and c[4] == "FAIL"]
    print(f"\n  newly BROKEN by the change: {len(newly_broken)}")
    for co, q, *_ in newly_broken:
        print(f"    BREAK {co} {q}")


if __name__ == "__main__":
    main()
