"""Census of hyphenated 항목번호 (sub-LOB legs) in the PL masters.

Question this answers: the 2026-08-29 leg-coverage rule in
`scripts/validate_master_tables.py` builds its 보험손익 closure from exactly three
LOB legs (생명장기손익 / 자동차손익 / 일반손익).  Reinsurers (and possibly others)
publish a *fourth* LOB whose 항목번호 is hyphenated ("2-1" = 장기재보험손익 for
코리안리).  This probe enumerates every hyphenated 항목번호 present in the root
master and in the viz master, per company/quarter, so we can tell whether the
equation's blind spot is 코리안리-only or general.

Read-only.  Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260829_hyphen_lob_census.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATHS = {
    "root PL_breakdown.json": ROOT / "PL_breakdown.json",
    "viz  pl_breakdown_master.json": ROOT / "data/dart/viz/pl_breakdown_master.json",
}


def main() -> None:
    for label, path in PATHS.items():
        rows = json.loads(path.read_text(encoding="utf-8"))
        print("=" * 78)
        print(f"{label}   rows={len(rows)}")
        print("=" * 78)

        hyph = [r for r in rows if isinstance(r.get("항목번호"), str) and "-" in r["항목번호"]]
        print(f"hyphenated 항목번호 rows: {len(hyph)}")

        # (항목번호, 항목명) -> set of companies, count
        by_item = defaultdict(lambda: {"companies": set(), "quarters": set(), "n": 0})
        for r in hyph:
            k = (r["항목번호"], r["항목명"])
            by_item[k]["companies"].add(r["원수사명"])
            by_item[k]["quarters"].add(r["공시분기"])
            by_item[k]["n"] += 1

        print(f"distinct (항목번호, 항목명): {len(by_item)}")
        for (no, name), info in sorted(by_item.items(), key=lambda x: (x[0][0], x[0][1])):
            cos = ", ".join(sorted(info["companies"]))
            print(f"  {no:>6s}  {name:<24s}  n={info['n']:>3d}  "
                  f"quarters={len(info['quarters']):>2d}  companies=[{cos}]")

        # which companies carry any hyphen item at all
        co_h = defaultdict(set)
        for r in hyph:
            co_h[r["원수사명"]].add(r["항목번호"])
        print(f"\ncompanies with any hyphen item: {len(co_h)}")
        for co, nos in sorted(co_h.items()):
            print(f"  {co:<18s} {sorted(nos, key=lambda s: (int(s.split('-')[0]), s))}")

        # name-collision check: does a hyphen item's 항목명 collide with a plain item's?
        plain_names = {r["항목명"] for r in rows
                       if not (isinstance(r.get("항목번호"), str) and "-" in r["항목번호"])}
        hyph_names = {r["항목명"] for r in hyph}
        collide = sorted(plain_names & hyph_names)
        print(f"\n항목명 collisions (hyphen vs plain): {len(collide)}")
        for n in collide:
            print(f"  COLLIDE  {n}")
        print()


if __name__ == "__main__":
    main()
