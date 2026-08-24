# -*- coding: utf-8 -*-
"""tier2 미검출 71건의 상세 사유(UNREADABLE/3키워드없음/라벨매칭실패) 를 나열."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from fix_20260821_tier2_limit_lines import _pdf, extract_tier2, q2p  # noqa: E402

MASTER = REPO / "kics_disclosure.json"


def main() -> int:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    by_c: dict[str, set] = {}
    name = {}
    for r in rows:
        c, q = r["원보험사코드"], r["공시분기"]
        by_c.setdefault(c, set()).add(q)
        name[c] = r.get("원수사명", c)

    for c in sorted(by_c):
        for q in sorted(by_c[c]):
            pdf = _pdf(q2p(q), c)
            if pdf is None:
                continue
            found, reason = extract_tier2(pdf)
            if not found:
                print(f"{c} {name[c]:<16} {q}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
