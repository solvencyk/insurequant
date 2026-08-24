# -*- coding: utf-8 -*-
"""orchestrator 발주(2026-08-22) — TFI(공통적용경과조치, item47-51) "no_table" 버킷 38건 중
이 세션이 맡은 6개사×1분기 singles backlog를 닫는다. 6개는 각각 parser-kics 서브에이전트가
독립 병렬조사(읽기전용, kics_disclosure.json 미접근)한 결과이고, 원인이 전부 다르다:

  KR0005 흥국화재   2024.4Q -- 스캔(이미지-only 필링, 표는 p41[1-idx]) -> vision 판독으로 적재가능
  KR0009 현대해상   2023.1Q -- 원문 3곳("요약표"/"4-2 개요표"/해당 섹션)이 전부 "해당사항 없음"
                                명시. 2023.2Q부터는 정상 공시(provenance already ITEM48_ANCHOR
                                전분기 일치) -- 이 분기만 진짜 미신청. **적재하지 않음.**
  KR0049 악사손해보험 2024.3Q -- 지급여력비율 섹션 전체가 "2024년 12월말 공시 예정"(보험업감독
                                규정 부칙 제3조) 규제유예. TODO.md L221에 이미 등재된 미공시
                                (items 1/14/27/28)와 동일 회사·분기의 47-51 확장 재확인.
                                **적재하지 않음.**
  KR0050 하나손해보험 2023.1Q -- K-ICS 시행 첫 분기 초기양식: "해당사항 없음"이면 표 자체를
                                안 찍음(각주만). 2023.2Q부터는 "해당사항 없음"이어도 6줄 표를
                                찍는 걸로 양식이 바뀜(대조군으로 직접 확인, 마스터 기존값과
                                일치). **적재하지 않음.**
  KR0069 삼성생명   2025.4Q -- 텍스트스트림이 [값_후,값_전,라벨] 순으로 나오는 반전 레이아웃.
                                기존 자동추출(extract_tfi_full)은 "라벨 다음 줄"을 잡아서 전부
                                한 칸씩 밀린 값(예: found47=진짜 item48 값)을 오탐으로 실었다 --
                                이 스크립트는 좌표(get_text("words"), 2가지 독립 재구성 방법
                                일치) + get_pixmap(dpi=250) 육안 대조로 재확정한 값만 쓴다.
  KR0073 교보생명   2023.1Q -- 교보 특유 순서뒤섞임의 새 하위유형: 표1의 숫자 12줄이 전부
                                먼저 나오고 라벨 30여개가 통째로 뒤에 몰린다(교집합 0줄) --
                                기존 2024.4Q/2025.4Q 사례("라벨 바로 뒤 엉뚱한 값")와 다른
                                패턴이라 "페이지는 찾았으나 못 읽음"으로 남아있었다. 좌표(y)
                                매칭으로 라벨-값 대응 복구.

## 값 출처와 단위

전부 raw PDF 원문 백만원 표기를 확인 후 ÷100 -> 억원(마스터 단위)으로 이미 환산된 값이다
(아래 딕셔너리는 최종 억원 값). 자체검산(모두 통과, 상세는 각 회사 섹션 코멘트):
  - item50+item51 ≈ item1 (전·후 각각) -- 3사 전부 diff <= 0.35억
  - item48 ≈ (그 표 자신의 지급여력기준금액 종결행, 또는 없으면 마스터 item14_전) × 50%
  - KR0073: item51 = min(item47,item48) 도 diff 0.0000(완전일치)로 추가 확인됨
  - KR0005: 마스터에 이미 있던 item2_후/item3_후 값이 이번에 읽은 item50_후/item51_후와
    소수 둘째자리까지 정확히 일치(다른 경로로 이미 검증된 값과 우연한 교차일치 -- 강한 방증)

## 적재하지 않는 3건 (참고용 레지스트리, 이 스크립트는 INSERT 안 함)

NOT_LOADABLE 딕셔너리에 사유만 남긴다 -- documented exception 등재(TODO.md)는 이 스크립트의
소관이 아니라 별도로 처리한다(오케스트레이터/validation 보고 대상). KR0049는 추가로 게이트
쪽 오분류 가능성도 있다(47_tier2_census 룰이 이 셀을 "추출갭"으로 RED 잡음 -- 원천 자체가
없는 건데 -- 이것도 validation 쪽 후속 처리 필요, 이 스크립트는 값만 다룬다).

Usage:
  ...python scripts/fix_20260822_singles_backlog.py --dry-run
  ...python scripts/fix_20260822_singles_backlog.py --dry-run --only KR0005
  ...python scripts/fix_20260822_singles_backlog.py   (실행은 오케스트레이터 승인 후)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"

ITEM_LABELS = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    50: "기본자본(TFI표, 공통적용경과조치)",
    51: "보완자본(TFI표, 공통적용경과조치)",
}

# --- 적재대상 3사×1분기 (억원, 전/후) ---
LOADABLE: dict[tuple, dict[int, tuple]] = {
    ("KR0005", "2024.4Q"): {  # 흥국화재, p41(1-idx), vision dpi150+280 교차확인
        47: (5749.13, 504.11),
        48: (9056.01, 9056.01),
        49: (16842.68, 16842.68),
        50: (5301.83, 7421.83),
        51: (22591.82, 20471.82),
    },
    ("KR0069", "2025.4Q"): {  # 삼성생명, idx56(0-idx)=p57, 좌표재구성+vision 대조
        # 이 회사는 각주로 "기발행 신종자본증권/후순위채무 없음 -> 전후 동일"을 명시,
        # 전=후 값이 진짜로 하나(원문도 컬럼 두 개가 같은 숫자를 반복 인쇄).
        47: (66288.79, 66288.79),
        48: (166037.63, 166037.63),
        49: (73369.68, 73369.68),
        50: (517743.32, 517743.32),
        51: (139658.46, 139658.46),
    },
    ("KR0073", "2023.1Q"): {  # 교보생명, p8(0-idx7), 좌표(y) 매칭으로 라벨-값 복구
        47: (11088.99, 0.00),
        48: (41575.31, 41575.31),
        49: (0.00, 0.00),
        50: (118657.28, 129746.27),
        51: (11088.99, 0.00),
    },
}

# --- 적재불가 3사×1분기 (참고 레지스트리, INSERT 안 함) ---
NOT_LOADABLE = {
    ("KR0009", "2023.1Q"): (
        "표부재(원문 3곳 '해당사항 없음' 명시: 요약표/4-2 개요표/[지급여력비율의 경과조치 "
        "적용에 관한 사항] 섹션 본문). 2023.2Q부터는 정상 공시(provenance ITEM48_ANCHOR 일치)."
    ),
    ("KR0049", "2024.3Q"): (
        "지급여력비율 섹션 전체가 원문에 '2024년 12월말 공시 예정'(보험업감독규정 부칙 제3조) "
        "규제유예로 공란. TODO.md L221 기존 미공시(items 1/14/27/28)의 47-51 확장 재확인. "
        "게이트 47_tier2_census가 이 셀을 TIER2_TABLE_ABSENT_INTERMITTENT로 미등재 상태라 "
        "RED 오분류 가능성 있음 -- validation 후속 필요(이 스크립트 범위 밖)."
    ),
    ("KR0050", "2023.1Q"): (
        "표부재(초기양식). K-ICS 시행 첫 분기라 '해당사항 없음'이면 각주만 찍고 표 자체를 "
        "안 찍음. 2023.2Q부터는 '해당사항 없음'이어도 6줄 표를 찍는 걸로 양식 변경(대조군 "
        "확인, 마스터 기존 item47-51과 일치)."
    ),
}


def _fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    dry = "--dry-run" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    print(f"로드 전 row_count = {len(data):,}")

    existing = {(r["원보험사코드"], r["공시분기"], int(r["항목번호"])) for r in data}
    meta_by_code: dict[str, dict] = {}
    for r in data:
        meta_by_code.setdefault(r["원보험사코드"], {
            "원수사명": r.get("원수사명"), "티커": r.get("티커"), "생손보여부": r.get("생손보여부"),
        })

    new_rows = []
    for (code, q), items in LOADABLE.items():
        if only and code != only:
            continue
        meta = meta_by_code.get(code)
        if meta is None:
            print(f"  [WARN] {code} 행 자체가 마스터에 없음 -- 건너뜀")
            continue
        for item, (pre, post) in items.items():
            if (code, q, item) in existing:
                print(f"  [SKIP] {code} {q} item{item} 이미 존재 -- 덮어쓰지 않음")
                continue
            row = {
                "원보험사코드": code,
                "원수사명": meta["원수사명"],
                "티커": meta["티커"],
                "생손보여부": meta["생손보여부"],
                "항목번호": item,
                "항목명": ITEM_LABELS[item],
                "공시분기": q,
                "값": _fmt(pre),
                "값_적용후": _fmt(post),
            }
            new_rows.append(row)
            print(f"  INSERT {code} {q} item{item}({ITEM_LABELS[item]}) "
                  f"값={row['값']} 값_적용후={row['값_적용후']}")

    print(f"\n=== 적재불가 (참고, INSERT 안 함) ===")
    for (code, q), reason in NOT_LOADABLE.items():
        if only and code != only:
            continue
        print(f"  {code} {q}: {reason}")

    print(f"\n합계: INSERT {len(new_rows)}건 (기대 15건 = 3사 x 5항목, --only 미사용 시)")
    if dry:
        print("(dry-run; 파일 안 씀)")
        return 0
    if not new_rows:
        print("쓸 변경 없음")
        return 0

    data.extend(new_rows)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(new_rows)}행 INSERT, wrote {TARGET.name} "
          f"(row_count {len(data) - len(new_rows):,} -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
