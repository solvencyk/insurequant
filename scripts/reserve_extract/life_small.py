#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""법정준비금(항목5·6·7·8) 회사별 추출 -- 소형 생보 3사 + NH농협손보.

담당 4사 (`HANDLERS` 참조):

| 코드 | 회사 | 생손보 | 표 패턴 |
|---|---|---|---|
| KR0032 | NH농협손해보험 | **손보** | 증감내역 3행표(해약·대손) + 이익잉여금 구성내역 ⊕ 조정이익표(비상위험) |
| KR0072 | 케이디비생명보험 | 생보 | 증감내역 3행표(해약·보증) |
| KR0082 | DB생명보험 | 생보 | 이익잉여금의 내역 잔액표(해약·대손·보증) |
| KR0083 | 푸본현대생명보험 | 생보 | 증감내역 3행표(대손) / 결손금의 내역 ⊕ 조정이익표 |

손보(NH)만 **비상위험준비금**(item6, 손보 전용 법정준비금)이 있고, 생보 3사는 없다.
반대로 생보(케이디비·DB생명)에는 **보증준비금**(item8)이 있고 NH에는 없다.

## 이 4사에서 확인한 핵심 사실 -- `잔액` 행이 정답이다

세 회사(NH·케이디비·푸본현대)가 쓰는 "증감내역" 주석은 개념마다 정확히 3행이다:

```
<개념> 기 적립액          763,069
<개념> 적립 예정금액(주)   45,755
<개념> 잔액              808,824     <- 이 값이 owner 공식(기적립+예정)의 결과 그 자체
```

즉 **`잔액` 행을 읽으면 함정 4(중복 계상)를 원천적으로 피한다** -- 같은 사건이 조정이익표·
처분계산서에 부호를 뒤집어 또 나와도 손댈 필요가 없다. 실측 검산(전부 바이트 일치):
  NH 2026.2Q 해약: 763,069 + 45,755 = 808,824 (raw line 15793~15805)
  NH 2026.2Q 대손: 4,844 + (4,844-4,480=364 환입) = 4,480
  푸본현대 2023.4Q 대손: 47,622 + (47,622) 환입 = 0 -> 잔액 '-'
`잔액`이 '-'(파싱 불가)면 `combine(기적립, 예정)`으로 되돌아간다.

## 0과 미공시의 구분 (이 모듈의 규약)

- 표에 **숫자가 실제로 있고** 그 합이 0이면 `0.0`을 돌려준다(푸본현대 2023.4Q 대손:
  47,622 전액 환입 -> 진짜 0). 이건 "확정된 0"이라 미공시와 구분돼야 한다.
- 세 칸이 **전부 '-'**면 계산할 숫자가 없으므로 **키를 뺀다**(케이디비 보증준비금 2026.1Q~2Q).
  대시만 보고 0을 지어내지 않는다.

## 연결 vs 별도 -- 뒤엣것(별도/OFS)을 채택

DART 사업·분기보고서는 연결주석이 먼저, 별도(재무제표) 주석이 나중에 온다. 마스터가 별도
(OFS) 기준이므로 **같은 개념이 두 번 나오면 나중 표가 이긴다.** 두 값이 실제로 다른 실측:
  케이디비생명 2024.1Q 보증준비금 적립예정: 연결 3,119 / 별도 3,201
  DB생명 2025.4Q 대손준비금: 연결 22,462 / 별도 22,461
  DB생명 2024.1Q: 연결표에는 해약환급금준비금 행 자체가 없고 별도표에만 있다

계약·공용헬퍼·나머지 함정은 `common.py` docstring 참조.
"""
from __future__ import annotations

from scripts.reserve_extract.common import (
    FilingContext, ITEM_CONCEPTS, combine, is_excluded_caption, norm, num,
    scale_guard, strip_label,
)

_CONCEPTS = tuple(ITEM_CONCEPTS.values())

_ACCRUED, _PENDING, _BALANCE = "accrued", "pending", "balance"


def _cur(row: list) -> str | None:
    """당기 컬럼 셀. 이 4사가 쓰는 표는 전부 [구분, 당기(말), 전기(말)] 3칸이고, 당기가 유일
    컬럼일 때만 2칸이다(NH 2023.4Q 해약환급금 증감내역: 헤더가 ['구분','당기'] 하나뿐 --
    제도 첫해라 전기가 아예 없다). 두 경우 모두 당기는 인덱스 1.

    **인덱스 1을 쓰는 이유**: "첫 파싱되는 숫자를 스캔"하면 안 된다 -- 케이디비생명 2026.2Q
    보증준비금 `['보증준비금 기적립액', '-', '2,913']`처럼 당기가 진짜 대시이고 전기에만 값이
    있는 정당한 케이스에서 전기를 당기로 오독하게 된다. 5칸짜리 처분계산서 행(당기값이
    인덱스 1, 뒤가 빈칸)은 이 모듈이 아예 읽지 않으므로(캡션 배제) 특례가 필요 없다.
    """
    return row[1] if len(row) >= 2 else None


def _role(rest: str) -> str | None:
    """개념명 뒤에 남은 꼬리 문자열 -> 행의 역할. 실측된 변형만 인정한다.

    기적립액: "기 적립액"(NH·푸본) / "기적립액"(케이디비)
    예정액  : "적립 예정금액(주)"·"적립(환입)예정금액(주)"·"환입 예정금액(주)"(NH),
              "적립(환입)예정 금액"·"적립 예정 금액"·"환입 예정 금액"(케이디비),
              "적립(환입) 예정액"(푸본), "환입액"(푸본 2024.4Q -- 이 해만 '예정'을 뺐다)
    잔액    : "잔액"
    (`strip_label`이 각주표시 (주)/(주1)/(주2)/(*)를 이미 벗겨서 넘어온다.)

    "반영전 반기순이익"·"반영후 조정이익"·"반영후 주당 조정이익" 같은 조정이익표 행은
    전부 None으로 떨어져야 한다 -- 위 셋 중 어디에도 안 걸린다.
    """
    if rest == "기적립액":
        return _ACCRUED
    if rest == "잔액":
        return _BALANCE
    if "예정" in rest and ("적립" in rest or "환입" in rest):
        return _PENDING
    if rest == "환입액":
        return _PENDING
    return None


def _rollforward_notes(ctx: FilingContext) -> dict[str, float]:
    """'증감내역' 3행 주석에서 개념별 최종 적립액(백만원). `잔액` 행 우선.

    표 하나 안에서만 역할을 모은다(개념이 여러 표에 흩어져 있어도 섞지 않는다 -- 함정 4).
    같은 개념이 여러 표에 있으면 **나중 표가 이긴다**(별도/OFS 채택, 이 파일 docstring).
    예정액만 있고 기적립액·잔액이 둘 다 없는 표는 rollforward가 아니라 조정이익류 표이므로
    통째로 버린다 -- 푸본현대 "대손준비금 반영 후 조정손실" 표가 여기 걸린다(`is_excluded_
    caption`의 배제어는 "조정손익"이라 '조정손실'은 안 걸러진다).
    """
    out: dict[str, float] = {}
    for t in ctx.tables:
        if is_excluded_caption(t.caption):
            continue
        found: dict[str, dict[str, str | None]] = {}
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = strip_label(r[0])
            for concept in _CONCEPTS:
                if not lab.startswith(concept):
                    continue
                role = _role(lab[len(concept):])
                if role is not None:
                    found.setdefault(concept, {}).setdefault(role, _cur(r))
                break
        scale = ctx.find_unit(t.line_no)
        for concept, roles in found.items():
            if _BALANCE not in roles and _ACCRUED not in roles:
                continue
            v = num(roles.get(_BALANCE))
            if v is None:
                v = combine(num(roles.get(_ACCRUED)), num(roles.get(_PENDING)))
            if v is None:      # 세 칸 전부 '-' -> 미공시로 두고 키를 뺀다
                continue
            out[concept] = abs(scale_guard(v, scale, t.line_no))
    return out


def _balance_listing(ctx: FilingContext, caption_needle: str) -> dict[str, float]:
    """'이익잉여금 구성내역'/'이익잉여금의 내역'/'결손금의 내역' 류 **잔액 나열표**에서
    라벨이 개념명 그 자체인 행의 당기값(백만원).

    캡션을 정확한 조각으로 좁히는 이유: 같은 필링의 처분계산서·결손금처리계산서에도 라벨이
    "1. 대손준비금"인 FLOW 행이 있고 `strip_label`이 "1."을 벗기면 개념명과 글자가 똑같아진다.
    `is_excluded_caption`은 "처분계산서"만 알고 푸본현대가 쓰는 "결손금**처리**계산서"는
    모른다 -- 그래서 캡션 needle을 "결손금의내역"으로 잡으면 "결손금처리계산서의내역"은
    문자열상 포함되지 않아 자동으로 빠진다.

    괄호 병기형 캡션도 잡는다 -- 푸본현대 2023.1Q는 "이익잉여금(결손금)의 내역"이라 쓴다
    (2023.2Q~부터는 "결손금의 내역"으로 단순화). 괄호만 제거한 사본에도 needle을 대조하면
    "...금(결손금)의내역" -> "...금결손금의내역"이 되어 "결손금의내역"을 부분문자열로 잡는다.
    괄호를 지워도 "결손금처리계산서의내역"엔 "처리계산서"가 그대로 끼어 있어 오매칭 안 한다.
    (parser 2026-08-21, inbox/parser/20260820T2340Z)
    """
    out: dict[str, float] = {}
    for t in ctx.tables:
        cap = norm(t.caption)
        cap_noparen = cap.replace("(", "").replace(")", "")
        if is_excluded_caption(t.caption) or (
            caption_needle not in cap and caption_needle not in cap_noparen
        ):
            continue
        scale = ctx.find_unit(t.line_no)
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = strip_label(r[0])
            if lab not in _CONCEPTS:
                continue
            v = num(_cur(r))
            if v is None:      # '-' -> 앞선(연결) 표 값을 덮어쓰지 않는다
                continue
            out[lab] = abs(scale_guard(v, scale, t.line_no))
    return out


def _pending_from_adjusted_profit(ctx: FilingContext, concept: str) -> float | None:
    """'<개념> 반영후 조정이익' 표에서 그 개념의 당기 적립(환입)예정액. **부호를 뒤집는다.**

    이 표는 준비금 적립을 "당기순이익에서 빼는 금액"으로 프레이밍하므로 셀 부호가 준비금
    증감의 반대다. NH농협손보 2026.2Q 실측:
      "비상위험준비금 적립 예정금액 | (6,004)"  -> 준비금 증가 +6,004
      "대손준비금 환입 예정금액     |    364"   -> 준비금 감소  -364  (같은 필링의
       대손 증감내역표는 "(364)"로 반대 부호를 찍는다 -- 두 표가 서로 검산이 된다)

    캡션이 `is_excluded_caption`에 걸리는 표라 `rows_matching()`의 기본 경로로는 절대 못 읽지만,
    NH농협손보의 **비상위험준비금은 증감내역 3행표가 어느 분기에도 없어서** 예정액을 여기서
    밖에 못 얻는다. 그래서 캡션을 "<개념>반영후조정이익"으로 못박아 이 표만 콕 집어 읽는다.

    검산(3개 연도 독립 확인, 전부 바이트 일치): 이익잉여금 구성내역의 기적립액에 이 값을
    더하면 **다음 회계연도 필링의 기적립액**이 정확히 나온다 --
      2023.4Q 232,341 + 29,491 = 261,832 = 2024.1Q 이익잉여금구성내역 당분기말
      2024.4Q 261,832 + 24,635 = 286,467 = 2025.1Q  〃
      2025.4Q 286,467 + 17,018 = 303,485 = 2026.1Q  〃
    """
    for t in ctx.tables:
        if concept + "반영후조정이익" not in norm(t.caption):
            continue
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = strip_label(r[0])
            if not lab.startswith(concept) or _role(lab[len(concept):]) != _PENDING:
                continue
            v = num(_cur(r))
            if v is None:
                continue
            return -scale_guard(v, ctx.find_unit(t.line_no), t.line_no)
    return None


def extract_nh_nonlife(ctx: FilingContext) -> dict[int, float]:
    """KR0032 NH농협손해보험 -- 손보라 비상위험준비금(6)이 있고 보증준비금(8)은 없다.

    해약환급금(5)·대손(7)은 "(N) 당분기 및 전분기 중 <개념>의 증감내역" 3행표의 `잔액`.
    비상위험(6)만 그 3행표가 없어서 (a) "(N) 이익잉여금 구성내역" 표의 기적립액 +
    (b) 조정이익표의 적립예정액(부호 반전)으로 조립한다 -- 근거는
    `_pending_from_adjusted_profit` docstring의 3개 연도 롤포워드 검산.

    오탐 방지: 같은 필링의 "이연법인세자산의 내용" 표에도 `해약환급금준비금 (672,507)` /
    `비상위험준비금 (243,654)` 행이 있다(2023.4Q, 전기말 컬럼은 (782,507) -- owner가 지적한
    `NH농협손보 △782,507` 오탐의 정체가 이것이다). `is_excluded_caption("이연법인세")`가
    막고, 위 두 경로 모두 캡션을 좁혀 잡으므로 이중으로 안 걸린다.
    """
    out: dict[int, float] = {}
    roll = _rollforward_notes(ctx)
    listing = _balance_listing(ctx, "이익잉여금구성내역")
    for item, concept in ITEM_CONCEPTS.items():
        if concept in roll:
            out[item] = roll[concept]
            continue
        accrued = listing.get(concept)
        if accrued is None:
            continue
        v = combine(accrued, _pending_from_adjusted_profit(ctx, concept))
        if v is not None:
            out[item] = v
    return out


def extract_kdb_life(ctx: FilingContext) -> dict[int, float]:
    """KR0072 케이디비생명보험 -- 증감내역 3행표만 쓴다(해약환급금·보증준비금).

    **대손준비금(7)은 확정된 genuine zero인데 숫자가 없어서 키를 뺀다.** 2026.2Q 본문
    (raw line 22392): "하지만 당사는 미처분이익잉여금 부족으로 인해 보험업감독규정에 따른
    대손준비금을 적립하지 않았습니다." 2024.1Q~2025.4Q도 같은 취지의 문장뿐이라 표 자체가
    없다("당분기말 및 전기말 현재 대손준비금으로 적립한 내역은 없습니다"). 서술문에서 0을
    긁어내는 캡션 문자열 매칭은 `common.py`가 경고하는 종류의 취약한 휴리스틱이라 안 한다.

    보증준비금(8)은 2026.1Q부터 세 칸이 전부 '-'라 키가 빠진다(2025년 중 2,913 전액 환입
    완료: 2025.1Q~4Q 표가 기적립 2,913 / 적립(환입)예정 (2,913) / 잔액 '-' -> 0.0으로 잡힌다).
    """
    roll = _rollforward_notes(ctx)
    return {item: roll[c] for item, c in ITEM_CONCEPTS.items() if c in roll}


def extract_db_life(ctx: FilingContext) -> dict[int, float]:
    """KR0082 DB생명보험 -- 증감내역 3행표가 없고 "이익잉여금의 내역" 잔액표 하나가 정본.

    그 표의 값은 **이미 처분예정액이 반영된 누적 잔액**이라 따로 더하면 안 된다. 근거:
      · 각주 "(*) 처분예정금액입니다."(2023.4Q raw line 21976)가 (*)행이 처분 반영분임을 명시
      · 롤포워드가 정확히 닫힌다 -- 1,633,087(2023.4Q) + 184,044(2024 전입) = 1,817,131
        (2024.4Q) + 191,300(2025 전입) = 2,008,431(2025.4Q), 전입액은 처분계산서의 값
      · owner 확정 앵커 2023.4Q item5 = 1,633,087 (raw line 21952, 라벨 `해약환급금준비금(*)`,
        캡션 "21.6 이익잉여금 (1) 보고기간종료일 현재 이익잉여금의 내역...", 단위마커
        `(단위: 백만원)` line 21915)

    **처분계산서를 같이 읽으면 안 된다**: 같은 필링 line 22389에 `해약환급금준비금전입 |
    (1,633,087)`이 5칸 행으로 또 있는데 부호가 반대라, 둘을 더하면 정답이 0으로 상쇄된다
    (개발 중 실제로 이렇게 망가졌다). `is_excluded_caption("처분계산서")`가 막는다.

    "준비금 반영 후 조정손익" 표(2023.4Q line ~22148)도 쓰지 않는다 -- 전기 컬럼이 소급가정치
    라서다. 그 표 각주: "(*1) 해약환급금준비금 및 보증준비금 제도의 시행시기는 당기(2023년)
    부터이나, 전기초부터 적용을 가정하여 ... 전입액을 산출하였습니다."
    """
    listing = _balance_listing(ctx, "이익잉여금의내역")
    return {item: listing[c] for item, c in ITEM_CONCEPTS.items() if c in listing}


def extract_fubon_hyundai_life(ctx: FilingContext) -> dict[int, float]:
    """KR0083 푸본현대생명보험 -- 누적결손금 회사라 대손준비금(7) 외에는 아무것도 없다.

    해약환급금(5)·보증준비금(8)은 **회계정책 서술(주석 2.15/2.16)에만 나오고 금액이 붙은
    행이 어느 분기에도 없다.** 미처리결손금이 있으면 이 준비금들을 적립하지 않는 규정
    (보험업감독규정) 그대로다 -- 2025.4Q 자본 주석의 이익잉여금(결손금)은 (500,276)백만원.
    없는 걸 0으로 지어내지 않고 키를 뺀다.

    대손준비금(7)은 두 경로:
      · "보고기간종료일 현재 이익잉여금처분후/결손금처리후 대손준비금의 내역" 3행표 -> 잔액
        (2023.4Q: 47,622 기적립 + (47,622) 환입 = **0.0**, 잔액 행도 '-' -- 확정된 0)
      · 그 표가 없는 분기(2023.3Q)는 "결손금의 내역" 표의 47,622 + 조정이익표 예정액('-')
    2024.1Q부터는 양쪽 다 '-'라 키가 빠진다(2023년 중 전액 환입 후 재적립 없음).
    """
    out: dict[int, float] = {}
    roll = _rollforward_notes(ctx)
    listing = _balance_listing(ctx, "결손금의내역")
    for item, concept in ITEM_CONCEPTS.items():
        if concept in roll:
            out[item] = roll[concept]
            continue
        accrued = listing.get(concept)
        if accrued is None:
            continue
        v = combine(accrued, _pending_from_adjusted_profit(ctx, concept))
        if v is not None:
            out[item] = v
    return out


HANDLERS = {
    "KR0032": extract_nh_nonlife,
    "KR0072": extract_kdb_life,
    "KR0082": extract_db_life,
    "KR0083": extract_fubon_hyundai_life,
}
