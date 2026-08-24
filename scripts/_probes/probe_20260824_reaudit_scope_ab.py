# -*- coding: utf-8 -*-
"""Read-only: does the KR0068 failure mode (wrong item47 scope) explain any of the 5 buckets?

For each re-audit bucket, recompute the pinned axes under BOTH item47 readings
(EXCL = item47 is debt-only · INCL = item47 already contains item49) and report
which reading, if either, reproduces the disclosed figure.

Also prints which buckets actually cast each issuer's scope vote, so we can see
whether the vote leans on the exempted bucket itself (circular evidence).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

TARGETS = [("KR0003", "2023.1Q"), ("KR0003", "2024.4Q"), ("KR0003", "2025.1Q"),
           ("KR0003", "2026.1Q"), ("KR0004", "2025.1Q")]
TOL = 2.0


def main() -> None:
    from src.solvency.validation.kics_json_rules import (
        _group_records, _tier2_i47_scope_map, TIER2_ZERO_EPS,
    )

    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    buckets = {(b.code, b.quarter): b for b in _group_records(rows)}
    smap = _tier2_i47_scope_map(list(buckets.values()), TOL)

    print("=" * 104)
    print("A/B: pinned axes recomputed under BOTH item47 readings  (residual = disclosed - expected)")
    print("=" * 104)
    for key in TARGETS:
        b = buckets[key]
        v = b.values
        i2, i3, i4, i12, i13 = (v.get(n) for n in (2, 3, 4, 12, 13))
        i47, i48, i49 = v.get(47), v.get(48), v.get(49)
        i50, i51, i52 = v.get(50), v.get(51), v.get(52)
        print(f"\n### {key[0]} {key[1]}   scope in force = {smap.get(key[0], 'EXCL')} "
              f"(map entry: {smap.get(key[0])})")
        print(f"    item47={i47}  item48={i48}  item49={i49}  item3={i3}  item51={i51}")
        for label, debt in (("EXCL (47 is debt-only)", i47),
                            ("INCL (47 contains 49)", None if None in (i47, i49) else i47 - i49)):
            if debt is None or None in (i48, i49):
                print(f"    {label:<26} — inputs missing")
                continue
            exp_capped = min(debt, i48) + i49
            exc = max(0.0, debt - i48)
            line = f"    {label:<26} 보완자본기대={exp_capped:>12.2f}"
            if i3 is not None:
                line += f"  축B잔차={i3 - exp_capped:>12.2f}"
            if i51 is not None:
                line += f"  축F잔차={i51 - exp_capped:>10.2f}"
            line += f"  한도초과={exc:>10.2f}"
            print(line)
            if None not in (i2, i4, i12, i13):
                clamp = min(exc, i12)
                brid = i4 - (i12 - clamp) - i13
                print(f"        -> 다리 기대={brid:>12.2f}  실제 item2={i2:>10.2f}  "
                      f"축A잔차={i2 - brid:>10.2f}   (한도초과 클램프={clamp:.2f})")
        if None not in (i50, i51, i52):
            print(f"    축E  item50+item51={i50 + i51:.2f} vs item52={i52:.2f} "
                  f"-> 잔차 {i52 - (i50 + i51):.2f}   (스코프 무관)")

    print("\n" + "=" * 104)
    print("scope vote provenance — which buckets are DECISIVE for each issuer?")
    print("=" * 104)
    for code in ("KR0003", "KR0004"):
        print(f"\n  {code}:")
        any_row = False
        for (c, q), b in sorted(buckets.items()):
            if c != code:
                continue
            for post in (False, True):
                src = b.values_post if post else b.values
                i3, i47, i48, i49 = src.get(3), src.get(47), src.get(48), src.get(49)
                if None in (i3, i47, i48, i49):
                    continue
                if max(abs(i47), abs(i48), abs(i49)) <= TIER2_ZERO_EPS:
                    continue
                excl = abs(i3 - (min(i47, i48) + i49)) <= TOL
                incl = abs(i3 - (min(i47 - i49, i48) + i49)) <= TOL
                if excl == incl:
                    continue
                any_row = True
                print(f"     {q:<9} {'적용후' if post else '적용전'}  votes "
                      f"{'EXCL' if excl else 'INCL'}   (i47={i47} i49={i49} i3={i3})")
        if not any_row:
            print("     (no decisive bucket — falls back to EXCL)")


if __name__ == "__main__":
    main()
