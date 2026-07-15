"""Follow-on to round 3: KR0087 동양생명 2025.2Q surfaced as a new
continuity-break once 2025.1Q got filled (same "sandwich" peeling seen
throughout this session). Raw confirms the same zero-selective-transition
pattern as every other 동양생명 quarter checked this session
(data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf p.14-16: "당사는
공통적용 경과조치만 적용" + 지급여력기준금액 2,421,410=2,421,410 unchanged).
Mirror 16-23 = 전. UPSERT-only.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGET_FILES = [REPO / "kics_disclosure.json", REPO / "templates" / "kics_disclosure.json"]

VALUES = {16: 8837, 17: 19973, 18: 0, 19: 8674, 20: 6655, 21: 1419, 22: 3670, 23: 0}


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def main():
    data = json.loads(TARGET_FILES[0].read_text(encoding="utf-8"))
    written = []
    for r in data:
        if r["원보험사코드"] != "KR0087" or r["공시분기"] != "2025.2Q":
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
