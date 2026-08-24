# -*- coding: utf-8 -*-
"""KB손해(KR0010) 2025.1Q — 임무3(SOURCE_UNREADABLE_NOT_VERIFIED) 판독 부수 산출물.

raw(`data/disclosure/FY2025_Q1/raw/KR0010_KB손해보험.pdf`)는 fitz 텍스트가 실질 0(전 26p
10.0자/p) 이라 스캔본으로 분류돼 있었으나, `get_pixmap(dpi=220)` 렌더링으로 육안 판독하니
실제로는 벡터 텍스트(디지털 생성 PDF)가 폰트 임베딩 문제로 fitz 유니코드 매핑만 실패하는
케이스였다 — 화면에는 또렷하게 읽힌다.

p11(0-idx 10, 인쇄쪽수 "10") [지급여력비율 총괄]: 경과조치 전=후 정확히 동일
  (지급여력비율 182.16, 지급여력금액 115,701, 지급여력기준금액 63,515).
p16(0-idx 15, 인쇄쪽수 "15") [경과조치 적용 전 지급여력비율 세부] (단위:억원):
  1.생명장기손해보험위험액=59,603 · 3.시장위험액=31,978  ← 마스터 item17전/19전과 정확히 일치.
p17(0-idx 16, 인쇄쪽수 "16") [지급여력비율의 경과조치 적용에 관한 사항]:
  (1) 공통적용경과조치 표 — 적용전/적용후 전 행 숫자 동일(단위 백만원).
  (2) 선택적용경과조치 ①②③ 전부 "당사는 ~ 적용하지 않아 경과조치 전·후 금액 및 비율이
      동일함" 명시 각주.
  → 이 회사는 TFI·TAC·TIR·TER/TIRR **전부 미신청**임이 텍스트로 명시돼 있다. item17후=item17전·
    item19후=item19전 미러링은 이미 정확했다(마스터 손 안 댐, 값 동일).

부수(Task2 tier2 확장): p17 (1)공통적용표에서 항목47/48/49 3줄을 같은 근거로 추가한다
(백만원→억원 ÷100). 자동 스캐너가 이 회사를 스캔본으로 오분류해 건너뛴 셀이라 자동화 대신
이 판독을 근거로 수기 UPSERT한다.
  보완자본 한도 적용 전 = 6,627,484 / 6,627,484
  보완자본 한도        = 3,175,772 / 3,175,772
  해약환급금 부족분 상당액 중 해약환급금 상당액 초과분 = 5,187,915 / 5,187,915
검산: 보완자본(6,627,484) != min(한도적용전,한도)+초과분(3,175,772+5,187,915=8,363,687) —
이 회사도 한화생명·BNP카디프와 같은 패턴(공식이 보편적이지 않음, validation에 보고).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
TARGET = REPO / "kics_disclosure.json"

NEW_CELLS = [
    (47, "보완자본 한도 적용 전", round(6627484 / 100, 2), round(6627484 / 100, 2)),
    (48, "보완자본 한도", round(3175772 / 100, 2), round(3175772 / 100, 2)),
    (49, "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
     round(5187915 / 100, 2), round(5187915 / 100, 2)),
]


def fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    print(f"로드 전 row_count = {len(data):,}")

    info = None
    existing = set()
    for r in data:
        if r["원보험사코드"] == "KR0010":
            info = {"원수사명": r.get("원수사명"), "티커": r.get("티커"), "생손보여부": r.get("생손보여부")}
        if r["원보험사코드"] == "KR0010" and r["공시분기"] == "2025.1Q":
            existing.add(int(r["항목번호"]))
    assert info is not None

    new_rows = []
    for it, label, pre, post in NEW_CELLS:
        if it in existing:
            print(f"item{it} 이미 존재 — 스킵")
            continue
        new_rows.append({
            "원보험사코드": "KR0010",
            "원수사명": info["원수사명"],
            "티커": info["티커"],
            "생손보여부": info["생손보여부"],
            "항목번호": it,
            "항목명": label,
            "공시분기": "2025.1Q",
            "값": fmt(pre),
            "값_적용후": fmt(post),
        })
        print(f"INSERT item{it} {label}: 값={fmt(pre)} 값_적용후={fmt(post)}")

    if dry or not new_rows:
        print("(dry-run 또는 신규 없음; 파일 안 씀)")
        return 0

    data.extend(new_rows)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(new_rows)}행 INSERT, wrote {TARGET.name} (row_count {len(data)-len(new_rows):,} -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
