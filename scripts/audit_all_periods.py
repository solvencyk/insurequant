#!/usr/bin/env python3
"""Full-coverage audit: 39 insurers × 13 periods × 5 sources.

Unlike report_collection_status.py (single latest period), this sweeps every
period and classifies each empty cell as either STRUCTURAL (expected N/A) or a
REAL GAP (should be collected but isn't). Prints a per-source gap list.

Sources: disclosure / DART / KIDI / IR / bonds(자본성증권).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.report_collection_status import (  # noqa: E402
    LOSS, LIFE,
    DART_LISTED_SET, DART_NONLISTED, DART_GROUP_COVERS,
    IR_NOT_AVAILABLE, IR_GROUP_COVERS,
    KIDI_MAPPING, PERIOD_TO_YYYYMM,
    check_disclosure, check_dart, check_kidi, check_ir,
)

ALL = LOSS + LIFE
PERIODS = list(PERIOD_TO_YYYYMM.keys())  # FY2023_Q1 .. FY2026_Q1 (13)

# MG/예별: only FY2025_Q4 onward (사명변경/재출범). Earlier periods structural N/A.
MG = "KR0004_MG"
MG_FIRST = "FY2025_Q4"

# 서울보증(KR0150) disclosure: site (sgic.co.kr SPA) retains only 연간 경영공시 +
# the single latest quarter; older Q1-Q3 are not retrievable (rolled off), and
# SGI is not DART-listed (IPO withdrawn) so DART has no 분기보고서 either →
# these quarterly cells are structural 미발행, not collection gaps.
# Verified 2026-06-01 (SPA list shows only latest 1Q + one 연간 file per year).
SGI_QUARTERLY_STRUCTURAL = {
    ("KR0150", "FY2023_Q1"), ("KR0150", "FY2023_Q2"), ("KR0150", "FY2023_Q3"),
    ("KR0150", "FY2024_Q1"), ("KR0150", "FY2024_Q2"), ("KR0150", "FY2024_Q3"),
    ("KR0150", "FY2025_Q2"), ("KR0150", "FY2025_Q3"),
}

# 서울보증(KR0150) DART: 미상장(IPO 철회) → 분기/반기/사업보고서 DART 미공시.
# User decision 2026-06-01 ("서울보증 걍 버려") → 구조적 제외 (won't-fix).
DART_DROP = {"KR0150"}

# KIDI: 재보험사 / structural zero insurers (장기손보 신계약 거의 없음)
KIDI_STRUCTURAL_ZERO = {"KR1000", "KR1098"}  # 코리안리(재보험), 카카오페이(디지털, 장기 신계약 ~0)
# KIDI: latest quarter not yet released as of audit date.
# FY2026_Q1 (202603) was published by KIDI and collected 2026-06-03 → no longer
# skipped. (Re-add the next unreleased quarter here when sweeping a new period.)
KIDI_NOT_RELEASED: set[str] = set()

# IR 9 단독사 (the only ones expected to have IR)
IR_SINGLE = {"KR0001", "KR0003", "KR0008", "KR0009", "KR0011",
             "KR0068", "KR0069", "KR0079", "KR0087"}
# Known IR gaps that are external-constraint (not fixable / sourced elsewhere)
IR_KNOWN_EXTERNAL = {
    ("KR0069", "FY2023_Q1"), ("KR0069", "FY2023_Q2"), ("KR0069", "FY2023_Q3"),  # samsunglife rolloff
}
# 동양생명 (KR0087) IR via myangel 401 — covered by disclosure instead; all pre-2026 IR
IR_KNOWN_EXTERNAL |= {("KR0087", p) for p in PERIODS if p != "FY2026_Q1"}


def period_lt(a: str, b: str) -> bool:
    return PERIODS.index(a) < PERIODS.index(b)


# Universe code → acceptable disclosure file prefix(es). Some insurers were
# saved under a different KR token than the universe code:
#   AIA       → files use KR0080_…
#   KR0004_MG → files use KR0004_… (예별 / MG)
FILE_PREFIX_ALIAS = {
    "AIA": ["KR0080", "AIA"],
    "KR0004_MG": ["KR0004", "KR0004_MG"],
}

def has_disclosure_file(period: str, kr: str) -> bool:
    raw = ROOT / "data" / "disclosure" / period / "raw"
    if not raw.exists():
        return False
    prefixes = FILE_PREFIX_ALIAS.get(kr, [kr])
    for f in raw.iterdir():
        if f.is_file() and any(f.name.startswith(pfx + "_") for pfx in prefixes):
            return True
    return False


def audit_disclosure():
    gaps = []
    for kr, name in ALL:
        for p in PERIODS:
            if has_disclosure_file(p, kr):  # alias-aware (AIA→KR0080, MG→KR0004)
                continue
            # structural exceptions
            if kr == MG and period_lt(p, MG_FIRST):
                continue  # 예별 재출범 전
            if (kr, p) in SGI_QUARTERLY_STRUCTURAL:
                continue  # 서울보증 분기 미발행 (연간+최신분기만)
            gaps.append((kr, name, p))
    return gaps


def audit_dart():
    """REAL gaps = LISTED companies' missing periodic filings only.

    User decision (2026-05-31): 비상장사 감사보고서는 불필요 → NONLISTED/외국계
    (incl. AUDIT_REPORT_ANNUAL) absences are structural N/A, not gaps. This
    covers both Q1-Q3 (no 분기보고서) AND Q4 (only 감사보고서, which we skip).
    """
    gaps = []
    for kr, name in ALL:
        if kr in DART_NONLISTED:
            continue  # 비상장/외국계 — 감사보고서만 존재, 사용자 결정상 불필요
        if kr in DART_DROP:
            continue  # 서울보증 미상장 — DART 미공시, 사용자 결정상 drop
        for p in PERIODS:
            status, note = check_dart(p, kr)
            if status == "O":
                continue
            # MG pre-reestablishment
            if kr == MG and period_lt(p, MG_FIRST):
                continue
            gaps.append((kr, name, p, note))
    return gaps


def audit_kidi():
    gaps = []
    for kr, name in ALL:
        if kr not in KIDI_MAPPING:
            continue  # not mapped → not expected (서울보증/카카오 등)
        for p in PERIODS:
            if p in KIDI_NOT_RELEASED:
                continue  # latest quarter not published yet
            if kr in KIDI_STRUCTURAL_ZERO:
                continue  # 재보험사
            if kr == MG:
                continue  # 예별 장기손보 신계약 미보고 (structural)
            status, note = check_kidi(p, kr)
            if status == "O":
                continue
            gaps.append((kr, name, p, note))
    return gaps


def audit_ir():
    gaps = []
    for kr, name in ALL:
        if kr not in IR_SINGLE:
            continue  # IR not expected (IR_NOT_AVAILABLE / group)
        for p in PERIODS:
            status, _ = check_ir(p, kr)
            if status == "O":
                continue
            if (kr, p) in IR_KNOWN_EXTERNAL:
                continue  # known external constraint, sourced elsewhere
            gaps.append((kr, name, p))
    return gaps


def main():
    print("=" * 70)
    print("FULL-COVERAGE AUDIT — 39 insurers × 13 periods × 5 sources")
    print("=" * 70)

    d = audit_disclosure()
    print(f"\n[정기경영공시] REAL GAPS: {len(d)}")
    for kr, name, p in d:
        print(f"   {kr:10s} {name:14s} {p}")

    dart = audit_dart()
    print(f"\n[DART 공시] REAL GAPS: {len(dart)}")
    for kr, name, p, note in dart:
        print(f"   {kr:10s} {name:14s} {p}  ({note})")

    kidi = audit_kidi()
    print(f"\n[보험개발원 KIDI] REAL GAPS: {len(kidi)}")
    for kr, name, p, note in kidi:
        print(f"   {kr:10s} {name:14s} {p}  ({note})")

    ir = audit_ir()
    print(f"\n[IR공시] REAL GAPS (단독 9사, 외부제약 제외): {len(ir)}")
    for kr, name, p in ir:
        print(f"   {kr:10s} {name:14s} {p}")

    print("\n" + "=" * 70)
    total = len(d) + len(dart) + len(kidi) + len(ir)
    print(f"TOTAL REAL GAPS (자본성증권 제외 — event-driven): {total}")
    print("=" * 70)
    print("""
NOTE — structural N/A (정상 공백, gap 아님):
  - 서울보증(KR0150): 분기 disclosure 미발행 + DART 미상장 → 전부 구조적 (사용자 drop 결정)
  - AIG(KR0029) Q2 = 반기(상반기) 누적 공시 (별도 2분기 없음); 신한EZ/카카오 Q2도 상반기
  - DART: NONLISTED 15사 Q1-Q3 (분기보고서 미공시, Q4 감사보고서만)
  - KIDI: 서울보증/카카오(미매핑), 코리안리(재보험), 예별(장기손보 미보고). FY2026_Q1은 2026-06-03 KIDI 발표분 수집 완료
  - IR: 단독 9사 외 30사 (그룹/외국계/비상장 — validation 지표 부재)
  - IR 외부제약: 삼성생명 FY23 Q1-Q3 (사이트 롤오프, 데이터는 4QFY23에 내장),
                동양생명 IR (myangel 401 → disclosure로 대체)
  - 자본성증권: event-driven (발행한 회사만) — 커버리지 개념 부적용
  - MG/예별: FY2025_Q4 이전 = 재출범 전 (해당없음)
""")


if __name__ == "__main__":
    main()
