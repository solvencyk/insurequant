# -*- coding: utf-8 -*-
"""2026.2Q 첫 게시사 하나손해보험(KR0050) 온보딩 후처리 (inbox
20260829T2130Z downloader raw-ready 통지 -> parser 처리).

fill_period_to_disclosure.py / fill_subitems_to_disclosure.py /
fill_market_subitems_to_disclosure.py 를 돌린 뒤 items 1-46 은 다 들어왔지만
(8_life・19_market・36_irr 전부 GREEN 재확인됨) 게이트 재실행에서 KR0050
2026.2Q 에 신규 RED 2건 + 구조적 게이트(continuity census) RED 1건이 남았다.
이 스크립트가 그 세 갈래를 KR0050 + 2026.2Q 셀에만 국한해 정정한다(다른
회사·분기는 절대 건드리지 않음 -- code/quarter 필터를 모든 루프에 강제).

## A. item28(기본자본비율) 결측 -> rule 8 RED
라벨이 원문에 문자 그대로 안 찍히는 파생값([[reference-kics-item28-computed]]
과 동일 패턴, scripts/recalc_kics_derived.py 의 관례를 그대로 재현하되 이
회사·분기 하나만 UPSERT). item28 = item2/item14*100.

## B. items 47-54 (TFI표, "[지급여력비율의 경과조치 적용에 관한 사항] (1)
공통적용" 표) 부분결측 + item48 오염 -> rule 47_tier2_census RED
"TIER2_PARTIAL_ROWS: [48] 는 있는데 [47, 49] 결측"

raw MD (md_inbox/FY2026_Q2/KR0050_하나손해보험.md L553-564, 단위 백만원) 원문:
    지급여력금액                    711,426  -> 52 (기존 "7114" 는 반올림 -- 7114.26 로 정밀화)
    기본자본                      104,887  -> 50 (기존 결측)
    보완자본                      606,539  -> 51 (기존 결측)
    보완자본 한도 적용 전            200,783  -> 47 (기존 결측)
    보완자본 한도                  233,828  -> 48 (기존 저장값 "6065" 는 오염 -- item51[보완자본]
                                              값이 실수로 들어가 있었다. label matcher 가
                                              "보완자본 한도"와 "보완자본"을 혼동한 결과로 추정,
                                              근본원인 조사는 kics_disclosure_parser.py 소관 --
                                              이 스크립트는 데이터만 고친다)
    해약환급금부족분상당액중초과분      405,756  -> 49 (기존 결측)
    (기발행 신종자본증권)                  0  -> 53 (기존 결측, 값 0)
    (기발행 후순위채무)                    0  -> 54 (기존 결측, 값 0)

자체검산(owner 확정 공식, fix_20260824_tfi_capital_memo_rows.py 도입):
    item51 == min(item47, item48) + item49 + item54
    6065.39 == min(2007.83, 2338.28) + 4057.56 + 0 == 2007.83 + 4057.56 == 6065.39  (exact)
스크립트가 쓰기 전에 이 항등식을 재확인하고, 안 맞으면 즉시 중단한다.

항목명 문자열은 KR0050 자신의 과거 12개 분기(2023.2Q-2026.1Q, 전부 47-54
연속 공시)에서 그대로 복사 -- 새 라벨을 지어내지 않는다.

## C. 값_적용후 비적용사 미러링 -> `_post_transition_parent_census` 구조게이트
TRAILING RED: "item[1,2,3,14,15,16,17,18,19,20,21,22,23,27]후 결측 (인접분기
적용후 present -> 표 유실)"

KR0050 은 `_TRANSITION_APPLIERS`(18사 FSS 정본) 밖 -- 경과조치 비적용사다.
data/_derived/kics_transition_applicability.json 레지스트리: 2023.1Q 부터
2026.1Q 까지 13개 분기 전부 TFI/TAC/TIR/TER/TIRR/PCA_DEFER = X (RPT 만 O,
보고기한 연장이라 재무수치 무관). 이번 분기 raw 도 동일 확인:
  L549 "(1) 공통적용 경과조치 관련 : 해당사항 없음"
  L566 "(2) 선택적용 경과조치 관련 : 해당사항 없음"
[지급여력비율의 총괄] 표(L410-423)·4-2-3 최근 3개년 표(L645-656) 등 모든
"경과조치 후" 컬럼이 3개 분기(당분기·-1·-2) 전부 공란 -- 이 회사는 단 한
분기도 후 컬럼에 실제 숫자를 인쇄한 적이 없다.

KR0050 자신의 직전 2개 분기(2025.4Q 풀폼·2026.1Q 간이공시) 마스터를 보면
공시된 모든 항목(1-46, 47-54 포함)이 값_적용후 = 값 로 미러링돼 있다 -- 이
스크립트는 새 관례를 만드는 게 아니라 같은 회사의 기존 관례를 이번 분기에
동일하게 잇는다. 0 으로 채우는 게 아니라 원문이 명시한 "전후 동일" 을
그대로 반영하는 것.

items 1-13(자본 티어) 를 건드리는 게 위험한 유일한 이유는 TFI(공통) 경과조치가
자본 티어(기본<->보완자본)만 재배분할 수 있어서인데(fix_20260716_nonapplier_
requirement_mirror.py 참고), KR0050 은 TFI 도 X(공통조치조차 미신청) 이므로
그 실패모드 자체가 성립하지 않는다.

대상 항목: 1-28(전부, 24-26 은 이미 "0"), 29-46(29-35/36-40/41-46), 47-54
(위 B 에서 만든/고친 값 그대로 미러 -- 표에 후 컬럼 자체가 없지만 KR0050
자신의 과거 관례가 그랬다).

Usage: python scripts/fix_20260829_kr0050_2026q2_onboarding.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET = REPO / "kics_disclosure.json"

CODE = "KR0050"
QUARTER = "2026.2Q"


def _num(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def _fmt(x: float) -> str:
    s = f"{x:.2f}"
    if s.endswith("0"):
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def _fmt_ratio(x: float) -> str:
    s = f"{x:.8f}".rstrip("0").rstrip(".")
    return s or "0"


# B. items 47-54 raw values (억원, from md_inbox/FY2026_Q2/KR0050_하나손해보험.md
# "[지급여력비율의 경과조치 적용에 관한 사항] (1) 공통적용" table, 백만원/100)
TFI_MEMO = {
    47: ("보완자본 한도 적용 전", 200783 / 100),
    48: ("보완자본 한도", 233828 / 100),
    49: ("해약환급금 부족분 상당액 중 해약환급금 상당액 초과분", 405756 / 100),
    50: ("기본자본(TFI표, 공통적용경과조치)", 104887 / 100),
    51: ("보완자본(TFI표, 공통적용경과조치)", 606539 / 100),
    52: ("지급여력금액(TFI표, 공통적용경과조치)", 711426 / 100),
    53: ("(기발행 신종자본증권)(TFI표, 공통적용경과조치)", 0.0),
    54: ("(기발행 후순위채무)(TFI표, 공통적용경과조치)", 0.0),
}

# items whose 값_적용후 gets mirrored from 값 (C) -- everything disclosed this
# quarter for this non-applying company. 항목번호 -> None (mirror source is
# each row's own 값, filled in main() once item28/47-54 exist).
MIRROR_ITEMS = list(range(1, 29)) + list(range(29, 47)) + list(range(47, 55))


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))

    bucket = {r["항목번호"]: r for r in data if r.get("원보험사코드") == CODE and r.get("공시분기") == QUARTER}
    if not bucket:
        print(f"no rows found for {CODE} {QUARTER} -- run fill_period_to_disclosure.py first")
        return 1
    template = bucket[1]

    changes: list[str] = []

    # --- self-check BEFORE any write: item51 == min(47,48) + 49 + item54 ---
    m47, m48, m49, m54 = (TFI_MEMO[n][1] for n in (47, 48, 49, 54))
    expected51 = min(m47, m48) + m49 + m54
    actual51 = TFI_MEMO[51][1]
    if abs(expected51 - actual51) > 0.01:
        print(f"ABORT: self-check failed -- min(47,48)+49+54={expected51:.2f} != item51={actual51:.2f}")
        return 1
    print(f"self-check OK: item51 {actual51:.2f} == min(47,48)+49+54 {expected51:.2f}")

    # --- A. item28 = item2/item14 * 100 ---
    i2 = _num(bucket[2]["값"])
    i14 = _num(bucket[14]["값"])
    if 28 not in bucket and i2 is not None and i14:
        val28 = i2 / i14 * 100.0
        row28 = {
            "원보험사코드": template["원보험사코드"],
            "원수사명": template["원수사명"],
            "티커": template["티커"],
            "생손보여부": template["생손보여부"],
            "항목번호": 28,
            "항목명": "기본자본비율",
            "공시분기": QUARTER,
            "값": _fmt_ratio(val28),
        }
        data.append(row28)
        bucket[28] = row28
        changes.append(f"ADD item28 값={row28['값']} (=item2/item14*100={i2}/{i14}*100)")
    elif 28 in bucket:
        changes.append(f"SKIP item28 -- already present 값={bucket[28]['값']}")

    # --- B. items 47-54 ---
    for item_no, (name, val_eok) in TFI_MEMO.items():
        val_str = _fmt(val_eok)
        row = bucket.get(item_no)
        if row is None:
            new_row = {
                "원보험사코드": template["원보험사코드"],
                "원수사명": template["원수사명"],
                "티커": template["티커"],
                "생손보여부": template["생손보여부"],
                "항목번호": item_no,
                "항목명": name,
                "공시분기": QUARTER,
                "값": val_str,
            }
            data.append(new_row)
            bucket[item_no] = new_row
            changes.append(f"ADD item{item_no} 값={val_str} ({name})")
        else:
            old = row.get("값")
            if old != val_str:
                changes.append(f"FIX item{item_no} 값 {old!r} -> {val_str!r} ({name})")
                row["값"] = val_str
                row["항목명"] = name  # keep label in sync too (48's old row had it right already)
            else:
                changes.append(f"SKIP item{item_no} -- already correct 값={val_str}")

    # --- C. mirror 값_적용후 = 값 for every item disclosed this quarter ---
    # (경과조치 완전 비적용 확정 -- see module docstring). UPSERT-only: never
    # overwrite an existing 값_적용후.
    mirrored = 0
    for item_no in MIRROR_ITEMS:
        row = bucket.get(item_no)
        if row is None:
            continue
        if row.get("값_적용후") not in (None, ""):
            continue
        if row.get("값") in (None, ""):
            continue
        row["값_적용후"] = row["값"]
        mirrored += 1
    changes.append(f"MIRROR 값_적용후=값 for {mirrored} rows (items present, previously missing 값_적용후)")

    print(f"{'DRY-RUN: ' if dry else ''}{len(changes)} change groups for {CODE} {QUARTER}:")
    for c in changes:
        print(" ", c)

    if dry:
        return 0

    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(data)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
