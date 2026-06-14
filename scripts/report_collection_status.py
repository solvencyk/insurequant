#!/usr/bin/env python3
"""Generate downloader collection-status report for a given period.

Output: a markdown table per user spec (구분 / 사코드 / 사명 / 정기경영공시 /
자본성증권 발행 / DART 공시 / 보험개발원 통계 / IR공시 / 비고).

For each insurer in the universe (손보 + 생보), checks whether each of the 5
sources has data for the period. O = collected and non-empty; X = source did
not publish OR could not collect (note in 비고). 비고 explains any gap.

Usage:
  python scripts/report_collection_status.py --period FY2026_Q1
  python scripts/report_collection_status.py --period FY2026_Q1 --out docs/collection-status-2026q1.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

# Full universe (37 K-ICS + MG손보 + AIA — 39 total)
LOSS = [
    ("KR0001", "메리츠화재"),
    ("KR0002", "한화손보"),
    ("KR0003", "롯데손보"),
    ("KR0004_MG", "예별손해 (구 MG손해)"),
    ("KR0005", "흥국화재"),
    ("KR0008", "삼성화재"),
    ("KR0009", "현대해상"),
    ("KR0010", "KB손해"),
    ("KR0011", "DB손해"),
    ("KR0029", "AIG손해"),
    ("KR0032", "NH농협손해"),
    ("KR0049", "악사손해"),
    ("KR0050", "하나손해"),
    ("KR0051", "신한이지손해"),
    ("KR0150", "서울보증"),
    ("KR1000", "코리안리재보험"),
    ("KR1098", "카카오페이손해"),
]
LIFE = [
    ("KR0068", "한화생명"),
    ("KR0069", "삼성생명"),
    ("KR0070", "ABL생명"),
    ("KR0071", "흥국생명"),
    ("KR0072", "KDB생명"),
    ("KR0073", "교보생명"),
    ("KR0074", "라이나생명"),
    ("KR0075", "BNP파리바카디프"),
    ("KR0076", "iM라이프"),
    ("KR0079", "미래에셋생명"),
    ("KR0082", "DB생명"),
    ("KR0083", "푸본현대생명"),
    ("KR0087", "동양생명"),
    ("KR0094", "신한라이프"),
    ("KR0095", "메트라이프"),
    ("KR0097", "하나생명"),
    ("KR0099", "KB라이프"),
    ("KR0100", "처브라이프"),
    ("KR0104", "농협생명"),
    ("KR1010", "교보라이프플래닛"),
    ("KR1011", "IBK연금보험"),
    ("KR0080",    "에이아이에이생명"),
]

# IR group coverage (group IR covers multiple KRs).
# DECISION 2026-05-31: 금융지주 그룹 IR (KB금융/신한금융/농협금융)은 CSM배수/부문별 손익 등
# validation 핵심 지표가 누락된 경우가 많아 IR universe에서 SKIP. 자회사들은 IR 미제공 회사로 분류.
# DB손해 IR이 DB생명을 cover하는 case는 단독사 IR이므로 유지.
IR_GROUP_COVERS: dict[str, list[str]] = {
    "KR0011": ["KR0011", "KR0082"],  # DB손해 IR may cover DB생명
}

# DART group holding coverage — group 사업/분기보고서 connected at <corp_code>_<name>/ dir
DART_GROUP_COVERS: dict[str, tuple[str, str, list[str]]] = {
    # subsidiary_KR -> (group_corp_code, group_name, all_subs_covered)
    "KR0050": ("00547583", "하나금융지주", ["KR0050", "KR0097"]),
    "KR0097": ("00547583", "하나금융지주", ["KR0050", "KR0097"]),
    "KR0051": ("00382199", "신한지주", ["KR0051", "KR0094"]),
    "KR0076": ("00878915", "iM금융지주", ["KR0076"]),
}

# Companies known NOT to publish useful IR (CSM배수/부문별 손익 등 validation 지표 부재).
# IR universe = 9사 단독공시 only (메리츠/롯데/삼성화재/현대/DB손해/한화생명/삼성생명/미래에셋/동양).
# 그룹지주 IR (KB금융/신한금융/농협금융)은 CSM배수·부문별 손익 누락으로 validation 부적합 → 자회사 자체 IR 없음 처리.
# 코리안리는 재보험사 → CSM배수 산출 X.
IR_NOT_AVAILABLE: set[str] = {
    # 손보 — IR 자료 자체 없음 / validation 부적합
    "KR0002",  # 한화손보 (IR 공시자료 미제공사)
    "KR0004_MG",  # MG손해 (legacy)
    "KR0005",  # 흥국화재 (비상장 태광계열)
    "KR0010",  # KB손해 (KB금융그룹 IR 부적합 → 자회사 IR 없음)
    "KR0029",  # AIG (외국계, 한국 별도 IR 없음)
    "KR0032",  # NH농협손해 (농협금융지주 IR 부적합)
    "KR0049",  # 악사 (외국계)
    "KR0050",  # 하나손해 (하나금융지주 IR 부적합)
    "KR0051",  # 신한이지 (신한금융그룹 IR 부적합)
    "KR0150",  # 서울보증
    "KR1000",  # 코리안리 (재보험사, CSM배수 N/A)
    "KR1098",  # 카카오페이
    # 생보 — IR 자료 없음 / 그룹 IR 부적합
    "KR0070",  # ABL (외국계)
    "KR0071",  # 흥국생명 (비상장)
    "KR0072",  # KDB
    "KR0073",  # 교보생명 (사용자: IR 없음)
    "KR0074",  # 라이나
    "KR0075",  # BNP
    "KR0076",  # iM라이프
    "KR0083",  # 푸본현대
    "KR0094",  # 신한라이프 (신한금융그룹 IR 부적합)
    "KR0095",  # 메트라이프
    "KR0097",  # 하나생명 (하나금융지주 IR 부적합)
    "KR0099",  # KB라이프 (KB금융그룹 IR 부적합)
    "KR0100",  # 처브라이프
    "KR0104",  # 농협생명 (농협금융지주 IR 부적합)
    "KR1010",  # 교보라이프플래닛
    "KR1011",  # IBK연금
    "KR0080",     # 외국계
    # NOTE: KR0082 DB생명은 DB손보 IR에 합산될 수 있어 그룹 cover 유지 (IR_GROUP_COVERS).
}

# DART universe (verified 2026-05-30 via spot check FY2025_Q1):
# LISTED 24사 = files 분기보고서 quarterly (pblntf_ty=A), verified to have actual document.zip
DART_LISTED_SET = {
    # 손보 11
    "KR0001","KR0002","KR0003","KR0005","KR0008","KR0009","KR0010","KR0011",
    "KR0032","KR0150","KR1000",
    # 생보 13
    "KR0068","KR0069","KR0070","KR0071","KR0072","KR0073","KR0079","KR0082",
    "KR0083","KR0087","KR0094","KR0099","KR0104",
}
# DART NON-listed = 분기보고서 미공시. 감사보고서 (FY*_Q4 period) only.
DART_NONLISTED = {
    "KR0004_MG",  # 비상장
    "KR0029",     # AIG (annual audit only)
    "KR0049","KR0050","KR0051","KR1098",  # 손보 NON_LISTED
    "KR0074","KR0075","KR0076","KR0095","KR0097","KR0100","KR1010","KR1011","KR0080",  # 생보 NON_LISTED + foreign
}

# KIDI MAPPING (cbCmp ↔ KR)
sys.path.insert(0, str(ROOT))
from scripts.ingest_kidi_monthly_premium import MAPPING as KIDI_MAPPING  # noqa: E402

# Period → YYYYMM for KIDI
PERIOD_TO_YYYYMM = {
    "FY2023_Q1": "202303", "FY2023_Q2": "202306", "FY2023_Q3": "202309", "FY2023_Q4": "202312",
    "FY2024_Q1": "202403", "FY2024_Q2": "202406", "FY2024_Q3": "202409", "FY2024_Q4": "202412",
    "FY2025_Q1": "202503", "FY2025_Q2": "202506", "FY2025_Q3": "202509", "FY2025_Q4": "202512",
    "FY2026_Q1": "202603",
}

# Period quarter range for 자본성증권 issue check
PERIOD_TO_RANGE = {
    "FY2026_Q1": ("2026-01", "2026-04"),
    "FY2025_Q4": ("2025-10", "2026-01"),
    "FY2025_Q3": ("2025-07", "2025-10"),
    "FY2025_Q2": ("2025-04", "2025-07"),
    "FY2025_Q1": ("2025-01", "2025-04"),
    "FY2024_Q4": ("2024-10", "2025-01"),
    # ... add others as needed
}


def check_disclosure(period: str, kr: str) -> tuple[str, str]:
    """Return (O/X, note)."""
    raw_dir = ROOT / "data" / "disclosure" / period / "raw"
    if not raw_dir.exists():
        return ("X", "디렉토리 없음")
    matches = list(raw_dir.glob(f"{kr}_*"))
    if matches:
        return ("O", "")
    return ("X", "미수집")


def check_dart(period: str, kr: str) -> tuple[str, str]:
    raw_dir = ROOT / "data" / "dart" / period / "raw"
    if not raw_dir.exists():
        return ("X", "분기 디렉토리 없음")
    matches = list(raw_dir.glob(f"{kr}_*"))
    # Verify at least one match has actual document.zip (not just meta-only stub)
    real_matches = [m for m in matches if (m / "document.zip").exists() and (m / "document.zip").stat().st_size > 1000]
    if real_matches:
        return ("O", "")
    # Try group holding coverage
    if kr in DART_GROUP_COVERS:
        group_cc, group_name, _covers = DART_GROUP_COVERS[kr]
        group_dir = raw_dir / f"{group_cc}_{group_name}"
        if (group_dir / "document.zip").exists() and (group_dir / "document.zip").stat().st_size > 1000:
            return ("O", f"그룹 DART({group_name})에 합산")
    # No real doc — determine reason
    is_nonlisted = kr in DART_NONLISTED
    is_q4 = period.endswith("Q4")
    if is_nonlisted and not is_q4:
        return ("X", "DART 정기보고서 미공시 (비상장/외국계, 감사보고서만)")
    if kr not in DART_LISTED_SET and not is_nonlisted:
        return ("X", "DART 미상장 회사")
    # listed company but document.zip missing — failed download
    if matches:
        return ("X", "DART 다운로드 실패 (재시도 필요)")
    return ("X", "DART 미수집")


def check_kidi(period: str, kr: str) -> tuple[str, str]:
    yyyymm = PERIOD_TO_YYYYMM.get(period)
    if not yyyymm:
        return ("X", f"period→yyyymm 미정의")
    raw_dir = ROOT / "data" / "kidi" / period / "raw"
    if not raw_dir.exists():
        return ("X", "분기 디렉토리 없음")
    # File pattern: KR####_<yyyymm>.json
    matches = list(raw_dir.glob(f"{kr}_*.json"))
    if not matches:
        if kr not in KIDI_MAPPING:
            return ("X", "KIDI cbCmp 매핑 없음")
        return ("X", "미수집")
    # Check denominator
    try:
        data = json.loads(matches[0].read_text(encoding="utf-8"))
        rows = ((data.get("result") or {}).get("result")) or []
        if not rows:
            return ("X", "KIDI 미공시 (rows=0)")
        first = rows[0]
        v4 = float(first.get("ITEM_VAL4") or 0)
        v8 = float(first.get("ITEM_VAL8") or 0)
        if v4 + v8 == 0:
            # Could be structural N/A (재보험사, 자동차전문) or KIDI not yet released
            note = "KIDI 미공시" if period == "FY2026_Q1" else "구조적 N/A (재보험/자동차전문)"
            return ("X", note)
        return ("O", "")
    except Exception as e:
        return ("X", f"parse err: {e}")


def check_ir(period: str, kr: str) -> tuple[str, str]:
    # IR_NOT_AVAILABLE takes precedence — even if a group IR dir exists for this KR,
    # the user has decreed those don't carry useful validation metrics.
    if kr in IR_NOT_AVAILABLE:
        return ("X", "IR 미공시 회사")
    raw_dir = ROOT / "data" / "ir" / period / "raw"
    if not raw_dir.exists():
        return ("X", "분기 디렉토리 없음")
    # Direct match
    matches = list(raw_dir.glob(f"{kr}_*"))
    if matches:
        return ("O", "")
    # Check group IR coverage (only DB손해 → DB생명 now; others SKIP per user decision)
    for parent_kr, covers in IR_GROUP_COVERS.items():
        if kr in covers and kr != parent_kr:
            group_match = list(raw_dir.glob(f"{parent_kr}_*"))
            if group_match:
                gname = group_match[0].name.split("_", 1)[1] if "_" in group_match[0].name else group_match[0].name
                return ("O", f"그룹 IR({parent_kr} {gname})에 합산")
    return ("X", "미수집")


def check_bonds(period: str, kr: str) -> tuple[str, str]:
    """Check 2026.1Q bond issuance for this insurer."""
    if period not in PERIOD_TO_RANGE:
        return ("X", "range 미정의")
    bonds_root = ROOT / "data" / "bonds" / "normalized"
    if not bonds_root.exists():
        return ("X", "디렉토리 없음")
    latest = sorted(bonds_root.iterdir())[-1] if any(bonds_root.iterdir()) else None
    if not latest:
        return ("X", "수집 없음")
    bjson = latest / "bonds_by_insurer.json"
    if not bjson.exists():
        return ("X", "파일 없음")
    data = json.loads(bjson.read_text(encoding="utf-8"))
    insurer = data.get(kr)
    if not insurer:
        return ("X", "FSC 등록 채권 없음")
    bonds = insurer.get("bonds") or []
    start, end = PERIOD_TO_RANGE[period]
    in_period = [b for b in bonds if start <= str(b.get("issue_date",""))[:7] < end]
    if in_period:
        amounts = sum(int(b.get("issue_amount_won") or 0) for b in in_period)
        return ("O", f"{len(in_period)}건 신규발행 {amounts/1e11:.1f}천억원")
    return ("X", f"{period} 중 별도 자본성증권 발행 내역 없음")


def _short_note(label: str, mark: str, note: str, period: str) -> str | None:
    """Compact 비고 phrasing per user spec (single-message sentences)."""
    if mark == "O":
        # Positive notes worth mentioning
        if label == "자본성증권":
            return note  # e.g. "1건 신규발행 4.4천억원"
        if label == "IR" and note and "그룹" in note:
            return note
        if label == "DART" and note and "그룹" in note:
            return note
        return None
    # X cases
    if label == "자본성증권":
        if "발행 내역 없음" in note:
            return f"{period.replace('FY','').replace('_Q','.')}Q 중 별도 자본성증권 발행 내역 없음"
        if "FSC 등록 채권 없음" in note:
            return "자본성증권 미발행 회사"
        return f"자본성증권 {note}"
    if label == "DART":
        return note  # already user-friendly per check_dart
    if label == "KIDI":
        if "미공시" in note and period == "FY2026_Q1":
            return "KIDI 2026.1Q 데이터 미공시 (대기 중)"
        if "구조적 N/A" in note:
            return "KIDI 구조적 N/A (재보험·자동차전문)"
        if "매핑 없음" in note:
            return "KIDI 미커버 회사"
        return f"KIDI {note}"
    if label == "IR":
        if note == "IR 미공시 회사":
            return "IR 공시자료 미제공사"
        if note == "미수집":
            return "IR 미수집"
        return f"IR {note}"
    if label == "경영공시":
        if note:
            return f"경영공시 {note}"
    return None


def gen_row(sector: str, kr: str, name: str, period: str) -> dict:
    disc = check_disclosure(period, kr)
    bonds = check_bonds(period, kr)
    dart = check_dart(period, kr)
    kidi = check_kidi(period, kr)
    ir = check_ir(period, kr)

    # 전체자료 입수 완료 = all expected sources O.
    # Acceptable X: bonds 미발행, KIDI 미공시 (2026.1Q honest gap), DART 비상장사 (구조적),
    # IR 미공시 회사 (구조적).
    accept_bonds_x = bonds[0] == "X" and ("발행 내역 없음" in bonds[1] or "FSC 등록 채권 없음" in bonds[1])
    accept_kidi_x = kidi[0] == "X" and ("미공시" in kidi[1] or "구조적" in kidi[1] or "미커버" in kidi[1])
    accept_dart_x = dart[0] == "X" and ("정기보고서 미공시" in dart[1] or "미상장" in dart[1])
    accept_ir_x = ir[0] == "X" and ir[1] in ("IR 미공시 회사",)
    cond = (
        disc[0] == "O"
        and (bonds[0] == "O" or accept_bonds_x)
        and (dart[0] == "O" or accept_dart_x)
        and (kidi[0] == "O" or accept_kidi_x)
        and (ir[0] == "O" or accept_ir_x)
    )
    if cond:
        bigo = "전체자료 입수 완료"
    else:
        parts = []
        for label, pair in [
            ("자본성증권", bonds), ("DART", dart), ("KIDI", kidi),
            ("IR", ir), ("경영공시", disc),
        ]:
            n = _short_note(label, pair[0], pair[1], period)
            if n:
                parts.append(n)
        bigo = "; ".join(parts) if parts else ""

    return {
        "구분": sector,
        "사코드": kr,
        "사명": name,
        "정기경영공시": disc[0],
        "자본성증권 발행": bonds[0],
        "DART 공시": dart[0],
        "보험개발원 통계": kidi[0],
        "IR공시": ir[0],
        "비고": bigo,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--period", default="FY2026_Q1")
    ap.add_argument("--out", default=None, help="markdown output path (also prints to stdout)")
    args = ap.parse_args()

    rows: list[dict] = []
    for kr, name in LOSS:
        rows.append(gen_row("손해보험", kr, name, args.period))
    for kr, name in LIFE:
        rows.append(gen_row("생명보험", kr, name, args.period))

    # Render markdown table
    cols = ["구분", "사코드", "사명", "정기경영공시", "자본성증권 발행", "DART 공시", "보험개발원 통계", "IR공시", "비고"]
    lines = []
    lines.append(f"# 데이터 수집 현황 — {args.period}")
    lines.append("")
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for r in rows:
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")

    # Summary stats
    total = len(rows)
    full = sum(1 for r in rows if r["비고"] == "전체자료 입수 완료")
    lines.append("")
    lines.append(f"**총 {total}사** / 전체자료 입수 완료 **{full}사** ({full/total*100:.0f}%)")

    # Source-level fill rate
    src_keys = ["정기경영공시", "자본성증권 발행", "DART 공시", "보험개발원 통계", "IR공시"]
    lines.append("")
    lines.append("**Source별 수집률**:")
    for sk in src_keys:
        n_o = sum(1 for r in rows if r[sk] == "O")
        lines.append(f"- {sk}: {n_o}/{total} ({n_o/total*100:.0f}%)")

    out_md = "\n".join(lines) + "\n"
    print(out_md)
    if args.out:
        Path(args.out).write_text(out_md, encoding="utf-8")
        print(f"\n[wrote] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
