#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""법정준비금(항목5·6·7·8) 회사별 추출 -- 중소형 손보 5사.

담당 5사 (`HANDLERS` 참조). **전부 손해보험사**라 항목8(보증준비금)은 어디에도 없고
(생보 전용), 대신 항목6(비상위험준비금, 손보 전용 법정준비금)이 기본이다:

| 코드 | 회사 | 표 패턴 | 뽑히는 항목 |
|---|---|---|---|
| KR0150 | 서울보증보험 | 3행 잔액노트(연1회) ⊕ 요약재무정보 2행(분기) | 6·7 |
| KR0049 | 악사손해보험 | 이익잉여금 내역 잔액표 ⊕ 이익잉여금처분계산서 | 5·6·7(=0) |
| KR0050 | 하나손해보험 | 이익잉여금(결손금) 구성내역 잔액표 | 6 |
| KR0051 | 신한이지손해보험 | (준비금 공시 자체가 없음) | 없음 |
| KR1098 | 카카오페이손해보험 | (준비금 공시 자체가 없음) | 없음 |

## 이 그룹의 핵심 -- "이익잉여금 내역의 잔액 = 기적립액"이다

`tier2_audit`/`life_small`이 쓰는 3행 노트(`기적립액`/`적립(환입)예정액`/`잔액`)는
**서울보증만** 갖고 있고, 나머지 4사는 이익잉여금 구성내역 한 줄이 전부다. 그 한 줄이
기적립액인지 잔액인지가 이 모듈의 유일한 쟁점인데, **서울보증이 두 표를 같은 필링에 동시에
싣기 때문에 실측으로 확정된다** (FY2025_Q4 `20260323000639.xml`):

    line 21039  이익잉여금 구성내역   | 대손준비금            |    48,155  (천원)
    line 43389  감독규정 대손준비금 잔액| 대손준비금 기적립액    |    48,155
                                      | 대손준비금 적립(환입)예정액|  687,414
                                      | 대손준비금 잔액        |   735,569

즉 **이익잉여금 구성내역의 당기말 = 기적립액**이고, 여기에 처분계산서의 처분예정액을 더해야
owner 공식의 적립액이 된다. 악사에서도 롤포워드가 정확히 닫힌다(전기 컬럼으로 독립 검산):
    비상위험 3,798,723(전기말) + 4,101,740(전기 처분 적립) = 7,900,463(당기말) ✔
    해약환급금 79,424,630(전기말) + (2,157,032)(전기 처분 환입) = 77,267,598(당기말) ✔

## 처분계산서 부호는 **뒤집지 않는다** (NH농협손보와 반대)

`life_small._pending_from_adjusted_profit`은 조정이익표를 읽느라 부호를 반전시킨다. 여기서
읽는 건 조정이익표가 아니라 **이익잉여금처분계산서**라 셀 값이 이미 준비금 증감 부호다.
악사 FY2025_Q4 raw line 19425~19444가 그 자체로 검산이 된다 --
    "2. 이익잉여금처분액(이입액)"        (33,783,826)
      "(1) 비상위험준비금 적립"            2,117,749
      "(2) 해약환급금준비금 환입"        (35,901,575)
    2,117,749 + (-35,901,575) = -33,783,826  = 합계행과 바이트 일치
`is_excluded_caption("처분계산서")`가 이 표를 기본 경로에서 막으므로 캡션을
"이익잉여금처분계산서"로 못박아 콕 집어 읽는다(NH가 조정이익표를 집어 읽는 것과 같은 방식).

## 서울보증 -- 분기엔 잔액노트가 없다

3행 잔액노트("감독규정에 따른 <개념> 잔액")는 **사업보고서에만** 있다. 분기·반기보고서엔
`Ⅲ.재무에관한사항`의 요약재무정보 표 하단 메모행 2줄(`(<개념> 기적립액)` /
`(<개념> 적립(환입)예정액)`, 단위 원)뿐이라 그때는 `combine()`으로 합산한다. 두 경로가
같은 값을 준다는 것도 실측 확인 (FY2025_Q4 동일 필링):
    요약재무정보(원)  2,488,079,095,683 + (361,053,854,566) = 2,127,025,241,117
    잔액노트(천원)                                              2,127,025,241  ✔
라벨에 괄호가 붙어(`(대손준비금 기적립액)`) `strip_label`이 **뒤쪽 `)`를 못 벗기므로**
`_role()`이 꼬리 괄호를 직접 걷어낸다.

## 준비금 공시가 아예 없는 회사 (미공시 ≠ 0)

- **신한이지손해보험** FY2025_Q4: 필링 전체에서 `준비금`이 4번 나오는데 전부
  일반손해보험위험 설명문의 "준비금위험"이다(raw line 2039·2053·2054). 법정준비금 표 없음.
- **카카오페이손해보험** FY2024_Q4·FY2025_Q4: `준비금` **0회**. 문자열 자체가 없다.
둘 다 미처리결손금 회사라(신한이지 raw line 15197 `22. 결손금처리계산서`, 카카오페이
raw line 11995 `(6) 회사의 당기 및 전기 결손금처리계산서`) 이익잉여금에서 적립하는
법정준비금을 쌓을 재원이 없다. **0을 지어내지 않고 키를 뺀다.** 다만 두 회사도 다른 3사와
같은 경로를 타게 해서, 나중에 흑자 전환해 표가 생기면 코드 수정 없이 잡히게 해 둔다.

## 진짜 0 (악사 대손준비금)

악사 FY2025_Q4 이익잉여금 내역표(raw line 19327)는 `대손준비금(*2) | - | -`인데, 이건
미공시가 아니라 **잔액 0**이다 -- 같은 표의 합계행이 그 0을 포함해 정확히 맞는다:
    0 + 7,900,463 + 77,267,598 + (33,783,826) = 51,384,235 = 합계행(line 19352)
각주 (*2)(line 19359)도 적립 규정을 설명하며 "이익잉여금에서 ... 적립금을 차감한 금액을
한도로 합니다"라고 한도가 0임을 시사한다. 그래서 이 표 안의 대시는 `0.0`으로 읽는다
(`tier2_audit._cell`과 같은 규약: **확인된 준비금 표 안에서만** 대시=0).

계약·공용헬퍼·나머지 함정은 `common.py` docstring 참조.
"""
from __future__ import annotations

from scripts.reserve_extract.common import (
    FilingContext, ITEM_CONCEPTS, combine, is_excluded_caption, norm, num,
    scale_guard, strip_label,
)

_CONCEPTS = tuple(ITEM_CONCEPTS.values())

_ACCRUED, _PENDING, _BALANCE = "accrued", "pending", "balance"

_DASHES = ("-", "―", "－", "‐")

# 잔액 나열표 캡션. 실측된 것만 넣는다(추측 금지) --
#   악사   "당기말 및 전기말 현재 이익잉여금 내역은 다음과 같습니다. (단위: 천원)"
#   하나손보 "28. 이익잉여금 (1) 이익잉여금(결손금)의 구성내역"
_LISTING_CAPTIONS = ("이익잉여금내역", "이익잉여금(결손금)의구성내역")

# 처분예정액 출처. `is_excluded_caption("처분계산서")`가 막는 표라 캡션으로 콕 집어 읽는다.
_APPROPRIATION_CAPTION = "이익잉여금처분계산서"


def _cur(row: list) -> str | None:
    """당기(말) 셀의 **원문 문자열**. 없으면 None.

    인덱스 1이 원칙이다 -- "첫 숫자를 스캔"하면 당기가 진짜 대시이고 전기에만 값이 있는
    정당한 케이스에서 전기를 당기로 오독한다(`life_small._cur` docstring의 케이디비 사례).
    다만 **완전히 빈 칸**은 값이 아니라 레이아웃 산물이라 건너뛴다: 서울보증 감사보고서
    첨부(`20260323000639_00760.xml` line 469)의 재무상태표는 `[라벨, 주석, 당기, 전기]`라
    인덱스 1이 주석열(빈 칸)이다. 빈 칸과 대시는 다르다 -- 대시는 그대로 돌려준다.
    """
    for cell in row[1:4]:
        if norm(cell):
            return cell
    return None


def _cell_value(raw: str | None) -> float | None:
    """확인된 준비금 표 안의 셀 -> 숫자. **대시는 0.0**(미공시가 아니라 잔액 0).

    근거는 파일 docstring "진짜 0 (악사 대손준비금)" 절. 셀 자체가 없으면(`None`)
    그건 미공시라 `None`을 그대로 돌려준다.
    """
    if raw is None:
        return None
    if norm(raw) in _DASHES:
        return 0.0
    return num(raw)


def _role(rest: str) -> str | None:
    """개념명 뒤 꼬리 문자열 -> 3행 노트에서의 역할. 실측 변형만 인정한다.

    서울보증 라벨은 `(대손준비금 기적립액)`처럼 통째로 괄호에 싸여 있는데 `strip_label`은
    **앞 괄호만** 벗기므로 여기서 뒤 `)`를 걷어낸다.
      기적립액: "기적립액"
      예정액  : "적립(환입)예정액" · "적립예정액" · "환입 예정액"(FY2025_Q3)
      잔액    : "잔액"
    """
    rest = rest.rstrip(")")
    if rest == "기적립액":
        return _ACCRUED
    if rest == "잔액":
        return _BALANCE
    if "예정" in rest and ("적립" in rest or "환입" in rest):
        return _PENDING
    return None


def _rollforward(ctx: FilingContext) -> dict[str, float]:
    """`기적립액` 행을 서명으로 갖는 표에서 개념별 최종 적립액(백만원). `잔액` 행 우선.

    표 하나 안에서만 역할을 모은다(개념이 여러 표에 흩어져도 섞지 않는다 -- common.py 함정4).
    같은 개념이 여러 표에 나오면 **나중 표가 이긴다**: DART 필링은 연결주석이 먼저, 별도
    주석이 나중이고 마스터는 별도(OFS) 기준이다. 서울보증 FY2025_Q4 실측 -- 같은 3행 노트가
    연결(line 21119)·별도(line 43389)로 두 번 실리는데 잔액은 735,569로 동일하고,
    옆의 조정이익만 267,686,040(연결)/263,556,835(별도)로 갈린다.
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
            if _ACCRUED not in roles and _BALANCE not in roles:
                continue      # 예정액만 있는 표 = 조정이익류. 서명 미충족이라 버린다.
            v = _cell_value(roles.get(_BALANCE))
            if v is None:
                v = combine(_cell_value(roles.get(_ACCRUED)),
                            _cell_value(roles.get(_PENDING)))
            if v is None:
                continue
            out[concept] = abs(scale_guard(v, scale, t.line_no))
    return out


def _listing(ctx: FilingContext) -> dict[str, float]:
    """이익잉여금 (결손금) 구성내역 잔액표에서 라벨이 개념명 그 자체인 행의 당기값(백만원).

    캡션을 `_LISTING_CAPTIONS`로 좁히는 게 핵심이다. 좁히지 않으면 **이연법인세 일시적차이
    표**를 물어 음수가 나온다 -- 하나손보 FY2025_Q4 line 28677/28889의 캡션이 각각
    "가.당기"/"나.전기"뿐이라 `is_excluded_caption`을 그냥 통과하고, 그 표의
    `비상위험준비금` 행은 (14,885,774)·(10,243,851)이다(진짜 잔액은 11,610,903).
    악사도 같은 형태의 이연법인세 표를 두 개 갖고 있다(line 20378·20646).

    부호는 `abs()`로 고정한다(common.py 함정 2 -- 준비금 stock은 음수 불가).
    """
    out: dict[str, float] = {}
    for t in ctx.tables:
        cap = norm(t.caption)
        if is_excluded_caption(t.caption) or not any(n in cap for n in _LISTING_CAPTIONS):
            continue
        scale = ctx.find_unit(t.line_no)
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = strip_label(r[0])
            if lab not in _CONCEPTS:
                continue
            v = _cell_value(_cur(r))
            if v is None:
                continue
            out[lab] = abs(scale_guard(v, scale, t.line_no))
    return out


def _appropriation(ctx: FilingContext) -> dict[str, float]:
    """이익잉여금처분계산서에서 개념별 당기 처분예정액(백만원). **부호 그대로.**

    행 라벨은 `(1) 비상위험준비금 적립` / `(2) 해약환급금준비금 환입`이고 `strip_label`이
    글머리를 벗기면 개념명 + `적립|환입|전입`만 남는다. 값은 이미 준비금 증감 부호라
    반전하지 않는다 -- 근거는 파일 docstring의 합계행 검산.
    """
    out: dict[str, float] = {}
    for t in ctx.tables:
        if _APPROPRIATION_CAPTION not in norm(t.caption):
            continue
        scale = ctx.find_unit(t.line_no)
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = strip_label(r[0])
            for concept in _CONCEPTS:
                if not lab.startswith(concept):
                    continue
                if lab[len(concept):].rstrip("액") in ("적립", "환입", "전입"):
                    v = num(_cur(r))
                    if v is not None:
                        out[concept] = scale_guard(v, scale, t.line_no)
                break
    return out


def _listing_plus_appropriation(ctx: FilingContext) -> dict[int, float]:
    """`적립액 = 이익잉여금 구성내역 당기말(=기적립액) + 처분계산서 처분예정액`.

    구성내역에 없는 개념은 키를 뺀다(처분계산서에만 나오는 개념은 flow라 stock이 아니다).
    """
    listing = _listing(ctx)
    pending = _appropriation(ctx)
    out: dict[int, float] = {}
    for item, concept in ITEM_CONCEPTS.items():
        if concept not in listing:
            continue
        v = combine(listing[concept], pending.get(concept))
        if v is not None:
            out[item] = v
    return out


def extract_sgi(ctx: FilingContext) -> dict[int, float]:
    """KR0150 서울보증보험 -- 비상위험(6)·대손(7)만. 5·8은 애초에 없다.

    보증보험 계약에는 해약환급금이 없고 보증준비금은 생보 전용이라, 디스크의 6개 분기
    XML 전부에서 `해약환급금준비금`·`보증준비금` 문자열이 **0회**다(실측). 잡힌다면 다른
    표를 잘못 물린 것이다.

    사업보고서는 3행 잔액노트, 분기·반기는 요약재무정보 2행 -- 둘 다 `_rollforward`가
    같은 서명(`기적립액` 행)으로 처리한다. 오탐 후보 셋이 전부 `_role()`에서 None으로
    떨어진다(라벨이 개념명 단독이라 꼬리가 빈 문자열):
      · 이익잉여금 구성내역의 `비상위험준비금`(기적립액만이라 단독으로 쓰면 예정액 누락)
      · 반기보고서 `공시금액` 대사표(2026.2Q raw line 24122·24127)
      · 자본/이연법인세 표의 음수 행(FY2025_Q4 line 23912 `(499,016,215)`)
      · 이사회 의결사항 표의 `비상위험준비금 제도 개선사항 보고`(2026.2Q line 66788,
        lxml sourceline 65535 캡 구간 -- 값이 전부 대시라 이중으로 무해)
    """
    roll = _rollforward(ctx)
    return {item: roll[c] for item, c in ITEM_CONCEPTS.items() if c in roll}


def extract_axa(ctx: FilingContext) -> dict[int, float]:
    """KR0049 악사손해보험 -- 해약환급금(5)·비상위험(6)·대손(7=진짜 0).

    FY2025_Q4 `20260331003812_00760.xml` 기준 산식(단위 천원, 마커 line 19299):
      item5 = 77,267,598 + (35,901,575) =  41,366,023   -> 41,366.023 백만원
      item6 =  7,900,463 +   2,117,749  =  10,018,212   -> 10,018.212 백만원
      item7 =          0 +          없음 =          0   ->      0.0   백만원
    대손이 0인 근거와 처분계산서 부호 근거는 파일 docstring 참조.
    """
    return _listing_plus_appropriation(ctx)


def extract_hana_nonlife(ctx: FilingContext) -> dict[int, float]:
    """KR0050 하나손해보험 -- 비상위험(6)뿐. 미처리결손금 회사라 나머지는 없다.

    FY2025_Q4 `20260325000538_00760.xml`: 이익잉여금(결손금) 구성내역(line 27239, 천원)에
    `비상위험준비금 11,610,903`이 **당기말·전기말 동일**하고, 뒤따르는 결손금처리계산서
    (line 27278)에는 준비금 처분 행이 아예 없다 -- 미처리결손금 (221,019,971)천원이라
    이익잉여금에서 적립할 재원이 없어 잔액이 얼어붙은 상태다. 그래서 예정액 없이
    11,610.903백만원이 그대로 적립액이다.

    `해약환급금준비금`·`대손준비금`·`보증준비금`은 필링 전체에서 **0회**(실측). 이 회사가
    쓰는 유일한 오탐 후보는 이연법인세 표의 음수 행이고 `_listing`의 캡션 제한이 막는다.
    """
    return _listing_plus_appropriation(ctx)


def extract_shinhan_ez(ctx: FilingContext) -> dict[int, float]:
    """KR0051 신한이지손해보험 -- 디스크의 유일한 필링(FY2025_Q4)에 법정준비금 공시가 없다.

    `20260330001079_00760.xml`에서 `준비금`은 4회뿐이고 전부 일반손해보험위험 설명문이다
    (line 2039 "보험가격위험, 준비금위험, 대재해위험으로 구분하여 측정합니다",
     line 2053 "준비금 위험은 ... 준비금 부채가 장래 지급될 보험금을 충당하지 못할 위험").
    자본 주석은 `22. 결손금처리계산서`(line 15197)로 미처리결손금만 이월한다.
    **미공시라 키를 뺀다** -- 0을 지어내지 않는다. 흑자 전환해 표가 생기면 다른 4사와 같은
    경로로 자동으로 잡힌다.
    """
    return _listing_plus_appropriation(ctx)


def extract_kakaopay(ctx: FilingContext) -> dict[int, float]:
    """KR1098 카카오페이손해보험 -- 두 필링(FY2024_Q4·FY2025_Q4) 모두 `준비금` 0회.

    문자열 자체가 없어서 파싱할 대상이 없다. 2017년 이후 설립된 디지털 손보사이고
    `(6) 회사의 당기 및 전기 결손금처리계산서`(FY2025_Q4 raw line 11995)가 보여주듯
    누적 결손 상태라 이익잉여금 법정준비금을 쌓을 재원이 없다. 키를 뺀다.
    """
    return _listing_plus_appropriation(ctx)


HANDLERS = {
    "KR0049": extract_axa,
    "KR0050": extract_hana_nonlife,
    "KR0051": extract_shinhan_ez,
    "KR0150": extract_sgi,
    "KR1098": extract_kakaopay,
}
