# -*- coding: utf-8 -*-
"""Follow-on to fix_20260821_kr0097_2024q2_vision_ocr.py.

Loading item36(금리위험액=374.03, from p18) turned rule `36_irr` from SKIP (item36 was absent)
into RED: item36 present in an even quarter (2024.2Q) but the 6-scenario IRR table (items 41-46)
was missing - same "surfaced by loading the parent" gap as KR0087's 19_market case.

Found the source by rendering further pages of the same scanned PDF (fitz get_text()=0 chars,
page.get_pixmap(dpi=300), read visually): p27 (1-idx) = "② 금리위험액 현황", 당기(2024.2Q)
column, 단위 백만원:
  Ⅲ. 순자산가치: 충격전 -675,156 | 평균회귀 -667,946 | 금리상승 -651,590 | 금리하락 -704,441 |
                금리평탄 -708,812 | 금리경사 -630,635
  Ⅳ. 금리위험액: 37,403  (= item36, matches p18's 37,403 exactly - cross-page consistency)

Verified before writing: derive(item36) = sqrt(max(R_up,R_dn)^2 + max(R_flat,R_steep)^2) + R_mr,
R = item41 - scenario, all from the p27 table -> 374.03, matching disclosed item36=374.03 to the
2nd decimal (essentially exact, see scripts/_probes or scratch verify - diff 0.002).

값_적용후: p14's 경과조치 신청현황 lists TIRR(금리위험액 증가분 점진적 인식) = X (not applied),
and item36 is confirmed unchanged 전=후 (37,403->37,403, p18). There is no separate
post-transition 순자산가치 scenario table anywhere in this filing (matches the prior, unrelated
2026-08-21 finding that all 618 existing item41-46_적용후 cells in the master mirror 적용전
exactly - "경과조치 전/후 축 자체가 원천에 없다"). Mirror 41-46 후=전 for consistency with that
established, already-verified pattern - not a new assumption.

Usage:
  ...python scripts/fix_20260821_kr0097_2024q2_irr.py --dry-run
  ...python scripts/fix_20260821_kr0097_2024q2_irr.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"
CODE, Q = "KR0097", "2024.2Q"

LABELS = {
    41: "3-1-0. 금리위험 순자산가치(충격전)", 42: "3-1-1. 금리위험 순자산가치(평균회귀)",
    43: "3-1-2. 금리위험 순자산가치(금리상승)", 44: "3-1-3. 금리위험 순자산가치(금리하락)",
    45: "3-1-4. 금리위험 순자산가치(금리평탄)", 46: "3-1-5. 금리위험 순자산가치(금리경사)",
}
# p27 Ⅲ.순자산가치 row, 당기(2024.2Q), 백만원 -> 억원. genuinely negative (net asset value
# under stress, not a reserve-adjusted-income table - parentheses here ARE real negatives).
VALUES = {
    41: -675156 / 100.0, 42: -667946 / 100.0, 43: -651590 / 100.0,
    44: -704441 / 100.0, 45: -708812 / 100.0, 46: -630635 / 100.0,
}


def fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    before_row_count = len(data)
    before_combos = {(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) for r in data}

    by_item = {int(r["항목번호"]): r for r in data
               if r.get("원보험사코드") == CODE and r.get("공시분기") == Q}
    item36 = float(by_item[36]["값"])
    r_up = VALUES[41] - VALUES[43]
    r_dn = VALUES[41] - VALUES[44]
    r_flat = VALUES[41] - VALUES[45]
    r_steep = VALUES[41] - VALUES[46]
    r_mr = VALUES[41] - VALUES[42]
    derived36 = (max(r_up, r_dn) ** 2 + max(r_flat, r_steep) ** 2) ** 0.5 + r_mr
    diff = abs(derived36 - item36)
    print(f"검산: derive(36)={derived36:.4f} vs item36(master)={item36} diff={diff:.4f} (허용 max(2.0,5%*|expected|))")
    if diff > max(2.0, 0.05 * abs(derived36)):
        print("!! IRR derive 검산 실패 - 중단")
        return 1

    inserts = []
    for it in sorted(VALUES):
        if it in by_item:
            print(f"SKIP item{it}: 이미 존재")
            continue
        v = fmt(VALUES[it])
        inserts.append({
            "원보험사코드": CODE, "원수사명": "하나생명", "티커": by_item[1].get("티커"),
            "생손보여부": by_item[1].get("생손보여부"), "항목번호": it, "항목명": LABELS[it],
            "공시분기": Q, "값": v, "값_적용후": v,  # mirror: TIRR 미적용, 원문에 후 축 없음
        })
    print(f"\n삽입 예정 {len(inserts)}행:")
    for row in inserts:
        print(f"  item{row['항목번호']} {row['항목명']:<38} 값={row['값']:>10} 값_적용후={row['값_적용후']}")

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0
    if not inserts:
        return 0

    data.extend(inserts)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {TARGET.name}: +{len(inserts)}행")

    after_row_count = len(data)
    after_combos = {(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) for r in data}
    removed = before_combos - after_combos
    added = after_combos - before_combos
    print(f"census: row_count {before_row_count} -> {after_row_count} (delta {after_row_count-before_row_count}, "
          f"expected +{len(inserts)})")
    print(f"combo delta: +{len(added)} / -{len(removed)}")
    if removed:
        print(f"!! UNEXPECTED REMOVED: {removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
