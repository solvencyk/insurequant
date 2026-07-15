"""Follow-on to fix_20260715_round2_post_scr_breakdown.py: filling KR0104
2023.2Q item19(후) exposed the same census RED as 2026.1Q did in round 1 --
parent item19 present, children 36-40 missing. Raw values from
data/disclosure/FY2023_Q2/raw/KR0104_농협생명보험_amended.pdf p.14 (③표 --
the only active transition touching market risk this quarter). Cross-
verified: MARKET_M(36-40) reproduces item19=16191.70 to the cent
(scripts/_probes/verify_market_m_kr0104_2023q2.py). UPSERT-only.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGET_FILES = [REPO / "kics_disclosure.json", REPO / "templates" / "kics_disclosure.json"]

# raw (백만원), p.14 ③표: 금리 1,298,257 / 주식 403,544 / 부동산 261,348(unchanged) /
# 외환 262,607(unchanged) / 자산집중 0(unchanged)
VALUES = {
    36: 1_298_257 / 100,
    37: 403_544 / 100,
    38: 261_348 / 100,
    39: 262_607 / 100,
    40: 0.0,
}


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def main():
    data = json.loads(TARGET_FILES[0].read_text(encoding="utf-8"))
    written = []
    for r in data:
        if r["원보험사코드"] != "KR0104" or r["공시분기"] != "2023.2Q":
            continue
        n = r["항목번호"]
        if n in VALUES and r.get("값_적용후") in (None, ""):
            r["값_적용후"] = _fmt(VALUES[n])
            written.append((n, r["값_적용후"]))
    print(f"{len(written)} cells: {written}")
    for path in TARGET_FILES:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
