# -*- coding: utf-8 -*-
"""Scan every (code, quarter) tier2 extraction: how many hit the 'item48 approx 0'
scale shortcut, and of those, how many have 47 or 49 non-trivially nonzero (meaning
the shortcut's 'scale is moot since everything is 0' assumption is WRONG for them)?
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from fix_20260821_tier2_limit_lines import _pdf, q2p, extract_tier2  # noqa: E402

TARGET = REPO / "kics_disclosure.json"


def main():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    by_c: dict[str, set] = {}
    info: dict[str, dict] = {}
    for r in data:
        c, q = r["원보험사코드"], r["공시분기"]
        by_c.setdefault(c, set()).add(q)
        info.setdefault(c, {"원수사명": r.get("원수사명")})

    suspects = []
    for c in sorted(by_c):
        for q in sorted(by_c[c]):
            pdf = _pdf(q2p(q), c)
            if pdf is None:
                continue
            found, anchor, reason = extract_tier2(pdf)
            f48 = found.get(48)
            if f48 is not None and f48[0] is not None and abs(f48[0]) < 0.005:
                f47, f49 = found.get(47), found.get(49)
                nontrivial = []
                if f47 and (abs(f47[0]) >= 0.5 or abs(f47[1]) >= 0.5):
                    nontrivial.append(("47", f47))
                if f49 and (abs(f49[0]) >= 0.5 or abs(f49[1]) >= 0.5):
                    nontrivial.append(("49", f49))
                flag = " <-- MIXED (48=0 but 47/49 nonzero)" if nontrivial else ""
                print(f"{c} {info[c]['원수사명']} {q}: 48={f48} 47={f47} 49={f49}{flag}")
                if nontrivial:
                    suspects.append((c, q, nontrivial))

    print(f"\n총 item48≈0 케이스 중 47/49 비자명(nonzero) 혼재 = {len(suspects)}건")
    for s in suspects:
        print(f"  {s}")


if __name__ == "__main__":
    raise SystemExit(main())
