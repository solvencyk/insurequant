"""Follow-on to fix_20260715_post_scr_breakdown_gap.py: filling KR0104
2026.1Q item19(후) exposed a fresh coverage-census RED (parent item19
present, children 36-40 missing). Raw values from
data/disclosure/FY2026_Q1/raw/KR0104_농협생명보험.pdf p.21 (③표 -- the only
active transition touching market risk for this company; ①/② don't
decompose 36-40 at all). Cross-verified: MARKET_M(36-40) reproduces
item19=10865.69 to the cent (scripts/_probes/verify_market_m_kr0104.py).
UPSERT-only, idempotent.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGET_FILES = [REPO / "kics_disclosure.json", REPO / "templates" / "kics_disclosure.json"]

# raw (백만원), p.21 ③표: 금리 531,485 / 주식 549,141 / 부동산 301,874(unchanged) /
# 외환 377,816(unchanged) / 자산집중 0(unchanged)
VALUES = {
    36: 531_485 / 100,
    37: 549_141 / 100,
    38: 301_874 / 100,
    39: 377_816 / 100,
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
        if r["원보험사코드"] != "KR0104" or r["공시분기"] != "2026.1Q":
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
