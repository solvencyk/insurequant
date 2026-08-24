# -*- coding: utf-8 -*-
"""AIA(KR0080) 6분기 + KB손해(KR0010) 5분기의 마스터 현재 상태(item1/14/27/47/48/49/50/51)를 덤프."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "kics_disclosure.json"
OUT = REPO / "scripts" / "_probes" / "aia_kb_master_state_out.json"

QUARTERS = {
    "KR0080": ["2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"],
    "KR0010": ["2024.1Q", "2024.3Q", "2025.3Q", "2025.4Q", "2026.1Q"],
}
ITEMS = [1, 2, 3, 12, 13, 14, 27, 28, 47, 48, 49, 50, 51]


def main():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    idx = {}
    for r in data:
        c, q, it = r["원보험사코드"], r["공시분기"], int(r["항목번호"])
        idx[(c, q, it)] = {"값": r.get("값"), "값_적용후": r.get("값_적용후"), "항목명": r.get("항목명")}

    out = {}
    for c, qs in QUARTERS.items():
        out[c] = {}
        for q in qs:
            row = {}
            for it in ITEMS:
                v = idx.get((c, q, it))
                row[str(it)] = v
            out[c][q] = row

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
