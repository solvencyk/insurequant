#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""법정준비금(항목5·6·7·8) 본문-XML 추출 -- 잔여 4개사(손보 1 + 생보 3).

담당: KR0029 AIG손해보험(DART 등록명 `에이아이지손해보험`) / KR0075 비엔피파리바카디프생명보험 /
KR0100 처브라이프생명보험 / KR1010 교보라이프플래닛생명보험.

## 이 그룹이 다른 그룹과 다른 점

- **넷 다 연1회 공시**다. `FY2026_Q1`·`FY2026_Q2`의 raw 디렉터리에는 `{"no_filing": true}`
  meta.json만 있다(KR0029는 2026년 디렉터리 자체가 없다) -- 결측이 아니라 정당한 상태다.
  분기값을 합성하지 않는다.
- **셋(KR0075·KR0100·KR1010)은 미처리결손금 회사**다. 보험업감독규정 제7-4조가
  "미처리결손금이 있는 경우에는 미처리결손금이 처리된 때부터 대손준비금을 적립하도록 한다"고
  못박고 있어(비엔피파리바카디프 FY2025 `20260406004430_00760.xml` line 8507 원문),
  법정준비금이 아예 없거나 과거 적립분만 동결돼 있는 게 정상이다. 값이 안 나오는 걸
  파싱 실패로 오해하지 말 것 -- 아래 회사별 docstring에 근거 문장을 인용해 뒀다.
- 항목6(비상위험준비금)은 손해보험 전용이라 **KR0029에만** 있다. 나머지 셋에서 잡히면
  다른 표를 잘못 물린 것이다(`_NOTE_ALIASES`가 회사별로 갈리는 이유).

## 표 형태 2종 (전수 실측, 디스크상 10개 XML)

**(A) 적립내역 표** -- `<개념>기적립액` / `<개념>적립(환입)예정액` / (`<개념>잔액`) 행.
표 식별은 **캡션이 아니라 `<개념>기적립액` 행의 존재**로 한다(`tier2_audit.py`와 같은 규칙).
캡션은 앞쪽 무관한 문단을 잘못 붙잡는다 -- 실제로 AIG의 적립내역 표 캡션은 두 해 모두
"이 감사보고서는 감사보고서일 현재로 유효한 것입니다..."라는 감사보고서 상투구다.
이 한 줄 규칙이 아래 오탐을 전부 막는다(전부 실측):

  - 처브라이프 FY2022 `19.보험계약부채` 표의 `보증준비금 5,932`(생존301+사망5,404+생사혼합227)
    -- 보험부채 안의 **최저보증준비금**이지 이익잉여금 내 법정 보증준비금이 아니다. 같은 필링의
    이연법인세표가 같은 5,932를 `최저보증준비금`이라고 풀어 쓴다. 그 표엔 `기적립액` 행이 없다.
  - 비엔피파리바카디프의 `결손금처리계산서(안)` 안 `2.대손준비금` / `3.해약환급금준비금` 행
    -- `EXCLUDED_CAPTION_WORDS`는 `처분계산서`만 갖고 있어 **`처리계산서`는 캡션 필터를 통과한다**
    (결손 회사는 처분이 아니라 처리계산서를 낸다). 그래도 `기적립액` 행이 없어 걸러진다.
  - AIG 이연법인세 증감표의 `비상위험준비금 (14,829,443)` 음수 행(캡션 필터에도 걸리지만
    이중으로 막힌다).

**(B) 이익잉여금/미처리결손금 구성내역 표** -- 항목별 잔액을 한 줄씩 나열. 여기서는
**대시(`-`) = 0인 칸만** 읽는다(`_listing_zeros`). 숫자는 절대 안 읽는다 -- 그 숫자는 (A)의
`기적립액`과 같은 값이라 예정액을 놓치고, `기적립액`인지 `잔액`인지 표만 봐서는 구분되지
않기 때문이다(common.py 함정 4). 대시는 어느 쪽으로 읽어도 0이라 이 위험이 없다.

## `잔액`이 있으면 그게 답이다

(A)에 `잔액` 행이 있으면 그 값을 **그대로** 쓴다. 회사가 이미 `기적립액 + 적립(환입)예정액`을
계산해 놓은 값이라 owner 공식과 동치다. **`잔액`은 `기적립액`이 아니다** -- 위에 예정액을 또
더하면 값이 두 배가 된다. `잔액`이 없거나 대시면 `combine()`으로 합산한다.
"""
from __future__ import annotations

from scripts.reserve_extract.common import (FilingContext, combine, is_excluded_caption,
                                            norm, num, scale_guard, strip_label)

# 항목6은 손보 전용이라 KR0029에만 준다(파일 docstring 참조).
_LIFE_ALIASES = {5: ("해약환급금준비금",), 7: ("대손준비금",), 8: ("보증준비금",)}
_NONLIFE_ALIASES = {**_LIFE_ALIASES, 6: ("비상위험준비금",)}

_DASHES = ("-", "―", "－", "‐")

# (B) 구성내역 표임을 확인하는 동반 행. 준비금 행만 보고 판정하면 보험부채 구성표까지 물린다.
_EQUITY_ANCHORS = ("이익준비금", "미처리결손금", "미처분이익잉여금", "이월이익잉여금",
                   "차기이월미처리결손금")


def _kind(rest: str) -> str | None:
    """개념명을 뗀 나머지 라벨 -> accrued / pending / total / None.

    이 4개사가 쓰는 변형은 두 가지뿐이다(10개 XML 전수): `기적립액` / `적립(환입)예정액`,
    그리고 비엔피파리바카디프만 `잔액` 행을 추가로 낸다. 그래도 `환입`·`전입` 변형을 같이
    받아 두는 건 다른 그룹 모듈에서 실제로 관측된 변형이고 비용이 0이기 때문이다.
    """
    if rest == "기적립액":
        return "accrued"
    if rest == "잔액":
        return "total"
    if "예정" in rest and any(w in rest for w in ("적립", "환입", "전입")):
        return "pending"
    return None


# `tier2_audit._cell`/`._cur`와 같은 로직을 일부러 복제했다. 그쪽 private 헬퍼를 import하면
# 다른 세션이 소유한 모듈의 비공개 API에 결합돼 버린다(그 모듈이 리팩터링되면 이쪽이 깨진다).
def _cell(raw: str | None) -> tuple[float | None, bool]:
    """(값, 공시여부). **확인된 준비금 표 안에서는 `-`가 0을 뜻한다**(미공시가 아니라).

    실측: 비엔피파리바카디프 FY2024·FY2025 `대손준비금 적립(환입)예정액 -`(=적립도 환입도
    없음, 잔액은 기적립액 그대로) / 같은 회사 구성내역표의 `해약환급금준비금 -`(=진짜 0).
    """
    t = norm(raw)
    if t in _DASHES:
        return 0.0, True
    v = num(raw)
    return (v, True) if v is not None else (None, False)


def _cur(row: list) -> float | None:
    """당기(말) 셀. 첫 숫자를 스캔하지 않고 인덱스로 집는다.

    AIG FY2025 필링은 셀 사이에 빈 칸을 끼워 `['257,706,250,422', '', '293,826,090,623', '']`
    처럼 나오고(전기=293,826,090,623), 첫 숫자 스캔은 이런 표에서 우연히 맞을 뿐 전기가 당기로
    새는 사고를 못 막는다. 주석열 때문에 인덱스 1이 빈 칸일 때만 한 칸 넘어간다.
    """
    for cell in row[1:3]:
        v, ok = _cell(cell)
        if ok:
            return v
        if norm(cell):
            return None
    return None


def _match(lab: str, aliases: dict[int, tuple[str, ...]]) -> tuple[int, str] | None:
    """행 라벨 -> (항목번호, 개념명). 개념명으로 시작하지 않으면 None."""
    for item, names in aliases.items():
        hit = next((nm for nm in names if lab.startswith(nm)), None)
        if hit is not None:
            return item, hit
    return None


def _accrual_notes(ctx: FilingContext, aliases: dict[int, tuple[str, ...]]) -> dict[int, float]:
    """(A) 적립내역 표에서 {항목: 백만원}. 항목당 **첫 번째** 적격 표만 쓴다(합치지 않는다).

    적격 표 = `<개념>기적립액` 행을 **하나라도** 가진 표. `tier2_audit._p2_notes`는 개념마다
    전용 표가 따로 있는 회사들이라 개념별로 `기적립액`을 요구했지만, AIG는 세 개념을 **한 표**에
    싣고 그 해에 새로 생긴 준비금은 `기적립액` 행 자체를 생략한다. 실측: FY2023
    `20240403002101_00760.xml` line 1151에 `해약환급금준비금 적립(환입)예정액 293,826,090,623`
    (원)만 있고 `해약환급금준비금 기적립액` 행이 없다 -- IFRS17과 함께 2023결산에 신설된
    준비금이라 기적립액이 진짜 0이기 때문이다. 그래서 **표 단위로 적격 판정**한 뒤에는 그 안의
    pending-only 개념도 기적립액 0으로 받는다. 이 완화가 없으면 AIG 2023 항목5가 통째로 죽는다
    (이전 범용 추출기가 실제로 그랬다).
    """
    out: dict[int, float] = {}
    for t in ctx.tables:
        if is_excluded_caption(t.caption):
            continue
        parts: dict[int, dict[str, float]] = {}
        for r in t.rows:
            if not r or not r[0]:
                continue
            hit = _match(strip_label(r[0]), aliases)
            if hit is None:
                continue
            item, concept = hit
            k = _kind(strip_label(r[0])[len(concept):])
            if k is None:
                continue
            slot = parts.setdefault(item, {})
            if k in slot:
                continue
            v = _cur(r)
            if v is not None:
                slot[k] = v
        if not any("accrued" in p for p in parts.values()):
            continue                      # 적립내역 표가 아니다 (파일 docstring "표 식별")
        for item, p in parts.items():
            if item in out:
                continue
            # `잔액`은 이미 합계다 -- 위에 예정액을 또 더하면 두 배가 된다.
            val = abs(p["total"]) if "total" in p else combine(p.get("accrued"), p.get("pending"))
            if val is None:
                continue
            out[item] = round(scale_guard(val, ctx.find_unit(t.line_no), t.line_no), 6)
    return out


def _listing_zeros(ctx: FilingContext, aliases: dict[int, tuple[str, ...]]) -> dict[int, float]:
    """(B) 이익잉여금/미처리결손금 **구성내역** 표에서 대시(=0)인 개념만 {항목: 0.0}.

    숫자는 일부러 안 읽는다(파일 docstring 참조). 표 자체도 `_EQUITY_ANCHORS` 행이 같이 있는
    경우에만 인정한다 -- 준비금 행만 보고 판정하면 `보험계약부채 구성내역` 같은 표까지 물린다.

    실측 근거: 비엔피파리바카디프 FY2025 `20260406004430_00760.xml` line 8373-8375
    `해약환급금준비금 | - | -`, 같은 표에 `이익준비금(주1) 3,871,603`·`미처리결손금
    (55,505,979)`가 앵커로 들어 있다. FY2024 필링(`20250404003021_00760.xml` line 8321 표)도
    동일하고, 두 해 모두 결손금처리계산서가 `3.해약환급금준비금 -`으로 한 번 더 확인해 준다.
    """
    out: dict[int, float] = {}
    for t in ctx.tables:
        if is_excluded_caption(t.caption) or "구성내역" not in norm(t.caption):
            continue
        labels = [strip_label(r[0]) for r in t.rows if r and r[0]]
        if not any(lab in _EQUITY_ANCHORS for lab in labels):
            continue
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = strip_label(r[0])
            hit = _match(lab, aliases)
            if hit is None or _kind(lab[len(hit[1]):]) is not None:
                continue      # 개념명 단독 행만 (적립내역 표의 세부 행은 (A)가 처리한다)
            if norm(_first_value_cell(r)) in _DASHES:
                out.setdefault(hit[0], 0.0)
    return out


def _first_value_cell(row: list) -> str:
    """구성내역 표의 당기말 칸. `_cur`과 달리 원문 문자열을 그대로 준다(대시 판정용)."""
    for cell in row[1:3]:
        if norm(cell):
            return cell or ""
    return ""


def extract_aig(ctx: FilingContext) -> dict[int, float]:
    """KR0029 AIG손해보험 -- 디렉터리명은 `KR0029_에이아이지손해보험`. 항목5·6·7.

    ⚠ **DART 등록명이 `에이아이지손해보험`이라 `resolve_corp('AIG손해보험')`이 None을 준다**
    (corp_code `00983606`). 그리고 그 코드로도 FS API는 15개 분기 × OFS/CFS 전부 status `013`
    (데이터 없음)이라 **본문 XML이 유일한 소스**다 -- 폴백이 없다.

    표는 감사보고서 앞부분 재무상태표 옆 적립내역 블록(단위 **원**, FY2023 line 870 /
    FY2025 line 498, 각각 직전 line 865·493에 `(단위 : 원)` 마커). 세 개념이 한 표에 있고
    `잔액` 행은 없어서 `combine()`으로 합산한다. 같은 필링의 주석 5-1 교차표(단위 천원,
    개념이 **열**이라 이 파서가 안 건드린다)가 회사 자체 산수로 독립 검증을 준다:

      FY2023 `20240403002101_00760.xml`
        본문 표 line 1137~1151(원): 비상위험 62,769,222,196 + 1,035,220,669 = 63,804,442,865
                                    대손      95,744,785 + (80,655,028)      = 15,089,757
                                    해약      (기적립액 행 없음=0) + 293,826,090,623
        주석 5-1 line 4336~4339(천원) 잔액 행: 15,090 / 63,804,443 / **293,826,091** / 합계 357,645,624
      FY2025 `20260407002104_00760.xml`
        본문 표 line 792 등(원): 해약 257,706,250,422 + 57,693,759,204 = 315,400,009,626
                                 비상위험 63,992,277,109 + 178,947,235 = 64,171,224,344
                                 대손      14,544,027 + 1,198,973      = 15,743,000
        주석 5-1 line 2186~2189(천원) 잔액 행: 15,743 / 64,171,224 / **315,400,010** / 379,586,977

    ⚠ **257,706.250422는 FY2025의 답이 아니다.** 그건 FY2025 필링의 `기적립액`, 즉 **FY2024
    기말 잔액**이다(주석 5-1 전기말 잔액 열 line 2192가 같은 257,706,250천원). FY2025 답은
    315,400.009626백만원이다. 형제 디렉터리 `..._20260407002109`(연결본 00761)의 이익잉여금
    내역표에 보이는 `해약환급준비금 257,706,250`도 같은 이유로 기적립 부분이지 합계가 아니다.
    체인이 필링을 가로질러 닫힌다: 2023 잔액 293,826,090,623 = FY2025 필링의 전기 기적립액,
    2024 잔액 257,706,250,422 = FY2025 필링의 당기 기적립액.

    **FY2024는 디스크에 raw가 아예 없다**(downloader 몫). 값 자체는 위 FY2025 필링의 전기말
    열에 남아 있지만(해약 257,706.250 / 비상위험 63,992.277 / 대손 14.544), 다른 회사와 같은
    규약대로 **각 연도는 그 연도 필링의 당기 열**만 쓰므로 여기서 합성하지 않는다.

    연결본(00761)과 별도본(00760)은 준비금 수치가 동일하다 -- 어느 쪽이 들어와도 같은 답이
    나오므로 호출자가 파일을 고를 필요가 없다(FY2025 00761 line 464 표에서 확인).
    """
    return _accrual_notes(ctx, _NONLIFE_ALIASES)


def extract_bnp_cardif(ctx: FilingContext) -> dict[int, float]:
    """KR0075 비엔피파리바카디프생명보험 -- 디스크에 FY2024·FY2025 두 해. 항목5·7.

    (A) 대손준비금 전용 노트가 3행 전부를 낸다(단위 **천원**). FY2025
    `20260406004430_00760.xml` line 8547/8553/8559: 기적립액 166,460 / 적립(환입)예정액 `-` /
    **잔액 166,460** -> 항목7 = 166.460백만원. FY2024 `20250404003021_00760.xml` line
    8514 표도 같은 166,460이고, 두 해 구성내역표의 `대손준비금 166,460`이 한 번 더 맞춘다.
    두 해가 같은 값인 건 정상이다 -- 결손 회사라 적립도 환입도 못 한다(아래 인용).

    (B) 항목5는 **진짜 0**이다. 구성내역표 line 8373-8375가 `해약환급금준비금 | - | -`로
    항목을 명시적으로 나열한 뒤 대시를 찍었고, 결손금처리계산서 line 8488도 `3.해약환급금준비금
    -`로 같은 말을 한다. 근거 규정도 같은 필링 line 8507에 있다: "동 대손준비금은 ... 미처리
    결손금이 있는 경우에는 미처리결손금이 처리된 때부터 대손준비금을 적립하도록 합니다."
    미처리결손금은 FY2025 55,505,979천원 / FY2024 30,683,978천원으로 오히려 커지는 중이다.

    항목8(보증준비금)은 키를 뺀다. 구성내역표가 이익준비금·대손준비금·해약환급금준비금만
    나열하고 보증준비금 행 자체가 없다(=미공시). 이연법인세표의 `최저보증준비금 199,628`은
    보험부채 쪽 항목이라 법정 보증준비금이 아니다. 항목6은 생보사라 없다.

    ⚠ 이 회사는 과거 CSM에서 100배 단위사고 전례가 있다(`inbox/parser/20260730T0035Z`).
    준비금 노트는 두 해 모두 표 직전에 `(단위: 천원)` 마커가 명시돼 있고(line 8522·8330),
    표 위치가 1만줄 이내라 sourceline 65535 캡과 무관하지만 계약대로 `scale_guard()`를 통과한다.
    """
    out = _accrual_notes(ctx, _LIFE_ALIASES)
    for item, v in _listing_zeros(ctx, _LIFE_ALIASES).items():
        out.setdefault(item, v)
    return out


def extract_chubb_life(ctx: FilingContext) -> dict[int, float]:
    """KR0100 처브라이프생명보험 -- 디스크에 FY2022~FY2025 네 해. **네 해 모두 공시 없음**.

    네 필링 전수 검색 결과 `대손준비금`·`해약환급금준비금`·`이익준비금` 문자열이 **0건**이고,
    FY2025 `20260408003172_00760.xml`은 `비상위험준비금`·`보증준비금`까지 포함해 0건이다.
    FY2022~FY2024에 보이는 `보증준비금`은 전부 `19.보험계약부채` 표의 보험종류별 최저보증
    준비금(FY2022 당기말 5,932백만원 = 생존301+사망5,404+생사혼합227)이거나 이연법인세표의
    `최저보증준비금` 행이라 법정 보증준비금이 아니다 -- `_accrual_notes`의 `기적립액` 서명
    규칙이 이미 걸러낸다(둘 다 그 행이 없다).

    누적결손이 원인이다. FY2025 필링 line 20520 "(2) 당기 및 전기 중 회사의 결손금처리계산서는
    다음과 같습니다."가 여는 표(단위 백만원)는 `Ⅰ.미처리결손금 267,578` / `1.전기이월미처리
    결손금 279,969` / `2.당기순이익 (12,391)` / `Ⅱ.차기이월미처리결손금 267,578` **네 줄이
    전부**다 -- 준비금 적립 행이 아예 없다. 결손이 2,676억원 남아 있는 회사는 법정준비금을
    적립하지 않는다(비엔피파리바카디프 docstring에 인용한 보험업감독규정 제7-4조 취지).

    따라서 빈 dict가 정답이다. 하드코딩 대신 공용 추출기를 그대로 태워 두는 이유는, 결손이
    해소돼 준비금이 생기는 해가 오면 코드를 안 고쳐도 잡히게 하기 위해서다.
    """
    out = _accrual_notes(ctx, _LIFE_ALIASES)
    for item, v in _listing_zeros(ctx, _LIFE_ALIASES).items():
        out.setdefault(item, v)
    return out


def extract_kyobo_lifeplanet(ctx: FilingContext) -> dict[int, float]:
    """KR1010 교보라이프플래닛생명보험 -- 디스크에 FY2025 한 해뿐. **공시 없음**.

    `20260327001138_00760.xml` 전수 검색에서 `해약환급금준비금`·`비상위험준비금`·`대손준비금`·
    `보증준비금`·`이익준비금` 모두 **0건**이다. 자본 구성표(line 13853-13863)는 `결손금 |
    미처리결손금 | (183,291,632,758)`(원) 한 줄이고, 결손금처리계산서(line 13985, 단위 원)도
    `미처리결손금 183,291,632,758` / `전기이월미처리결손금 163,177,194,822` / `당기순손실
    20,114,437,936` / `결손금처리액 -` / `차기이월미처리결손금 183,291,632,758`가 전부다.
    결손이 1,833억원이고 매년 200억원씩 커지는 디지털 전업사라 법정준비금 적립 여지가 없다.

    처브라이프와 같은 이유로 하드코딩하지 않고 공용 추출기를 태운다.
    """
    out = _accrual_notes(ctx, _LIFE_ALIASES)
    for item, v in _listing_zeros(ctx, _LIFE_ALIASES).items():
        out.setdefault(item, v)
    return out


HANDLERS = {
    "KR0029": extract_aig,
    "KR0075": extract_bnp_cardif,
    "KR0100": extract_chubb_life,
    "KR1010": extract_kyobo_lifeplanet,
}
