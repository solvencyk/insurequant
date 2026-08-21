#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""법정준비금(항목5·6·7·8) -- 대형 생보 5사 본문-XML 추출.

| KR | 회사 | 표 패턴 | 별도(OFS) 블록 위치 |
|---|---|---|---|
| KR0068 | 한화생명 | 연도별로 3형태(내역표 / `기적립액`단표 / transposed) + 처분계산서 | 유일 블록(연결 주석엔 준비금 내역표 없음) |
| KR0069 | 삼성생명 | 연도별로 3형태(내역표 / P1 주석 / transposed) | 연결 뒤 두 번째 블록 |
| KR0073 | 교보생명 | P2 (`기적립액`/`적립(환입)예정액`/`잔액`) | 연결 뒤 두 번째 블록 |
| KR0094 | 신한라이프 | P2 (동일) | 연결 뒤 두 번째 블록(값은 연결과 동일) |
| KR0104 | 농협생명 | P1 (`기적립액`/`적립예정금액`/`예정잔액`) | 연결 뒤 두 번째 블록(값 동일) |

## 세 가지 설계 결정 (전부 실측 근거)

**(1) 왜 "별도(OFS)"인가.** 프로젝트 BS 규약이 전사 OFS 고정이다. 연결과 별도는 실제로
다르다 -- 교보생명 2026.2Q 대손준비금 잔액 연결 111,623 / 별도 107,397, 삼성생명 2026.2Q
대손준비금 연결 357,453 / 별도 299,321. 해약환급금준비금은 보험업감독규정상 보험사 단위
항목이라 두 기준이 같지만(삼성 832,412 동일), 대손준비금 때문에 기준을 반드시 골라야 한다.

**(2) 왜 `_pick`이 "인접 클러스터의 첫 표"인가.** DART 필링은 ① 연결 주석 블록이 먼저,
별도 주석 블록이 수백 표 뒤에 오고 ② 삼성·한화처럼 기간을 표로 쪼개는 회사는 (당기표,
전기표)가 바로 붙어 나온다. 그래서 "표 인덱스 간격 <= 8"로 클러스터를 묶고 **마지막
클러스터의 첫 표**를 고르면 두 축이 동시에 해결된다. 단순히 "마지막 표"를 쓰면 한화생명
2026.2Q에서 전기말 표(해약 3,631,206)를 당기말(6,507,790) 대신 집어 1년치가 밀린다.

**(3) 왜 lxml line_no를 못 믿나.** 한화생명·삼성생명 필링은 6.5만 줄을 넘어 모든 표가
`line_no=65535`로 캡된다(common.py 함정 3). 실제로 한화생명 2024.1Q 이익잉여금 내역표는
캡션이 "(단위:백만원)"인데 `find_unit`이 1e-6(원)을 돌려준다 -- 그대로 쓰면 2,504,752가
2.504752가 된다. 모든 값은 `scale_guard`를 통과시킨다.
"""
from __future__ import annotations

import re

from scripts.reserve_extract.common import (
    FilingContext, ITEM_CONCEPTS, combine, norm, num, scale_guard, strip_label,
)

# 모든 준비금 주석표는 [라벨, 당기, (전기)] 순이다 -- 5사 × 13분기 전수 확인.
# "첫 파싱되는 숫자"를 스캔하면 안 된다(당기가 '-'인 정당한 케이스에서 전기를 당기로
# 오인한다 -- build_equity_composition_tier2.py `_row_value`가 케이디비생명으로 이미 데인 함정).
_CUR = 1

# 적립예정액 접미사 변형. 실측 수집: 적립예정금액(농협)·적립예정액(교보)·적립(환입)예정액(교보/삼성)
# ·환입예정금액(농협/교보)·전입(환입)예정금액(농협/신한)·적립(이입)예정액(삼성 2023)
# ·전입예정금액(한화 2024.4Q)·적립(환입)예정금액(한화 2023.4Q).
_PENDING_RE = re.compile(r"^(적립|전입|환입)(\((환입|이입|전입|적립)\))?예정(금액|액|금)$")
_ACCRUED = ("기적립액", "기적립금")
_BALANCE = ("잔액", "예정잔액")


def _kind(rest: str) -> str | None:
    """개념명 뒤에 남은 접미사 -> 행 종류."""
    if rest in _ACCRUED:
        return "accrued"
    if rest in _BALANCE:
        return "balance"
    if _PENDING_RE.match(rest):
        return "pending"
    return None


def _scan(ctx: FilingContext, concept: str) -> dict[str, list]:
    """{kind: [(tidx, table, row)]} -- 문서 순서.

    캡션 배제(`is_excluded_caption`)를 쓰지 않는다. 이 5사에서 준비금 예정액이 실린 표는
    캡션이 거의 항상 "...조정이익..."(배제어)이고(교보·삼성·한화 전 분기), 반대로 캡션이
    앞 문단을 잘못 붙잡아 무의미한 경우도 흔하다(한화 2026.2Q 준비금표 캡션 = "종속기업
    투자의 공정가치..."). 대신 라벨을 `<개념>+<정확한 접미사>`로 좁게 잠가 함정 1(이연법인세
    표·조정이익표 오탐)을 막는다 -- 그 표들의 행은 "...환입(전입)액"·"기초 누적일시적차이"
    처럼 접미사가 달라 여기 걸리지 않는다.
    """
    out: dict[str, list] = {}
    for i, t in enumerate(ctx.tables):
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = strip_label(r[0])
            if not lab.startswith(concept):
                continue
            k = _kind(lab[len(concept):])
            if k:
                out.setdefault(k, []).append((i, t, r))
    return out


def _pick(cands: list, gap: int = 8):
    """후보들 중 '별도(OFS) · 당기' 하나. 위 docstring (2) 참조."""
    if not cands:
        return None
    cluster = [cands[0]]
    for c in cands[1:]:
        if c[0] - cluster[-1][0] <= gap:
            cluster.append(c)
        else:
            cluster = [c]
    return cluster[0]


def _val(ctx: FilingContext, t, row, idx: int = _CUR) -> float | None:
    """행의 당기 셀 -> 백만원 (단위 적용 + 매그니튜드 방어)."""
    if idx >= len(row):
        return None
    v = num(row[idx])
    if v is None:
        return None
    return scale_guard(v, ctx.find_unit(t.line_no), t.line_no)


def _from_notes(ctx: FilingContext, concept: str) -> float | None:
    """준비금 주석표(P1/P2)에서 최종 적립액.

    `잔액` 행이 있으면 그게 정본이다 -- 원표에서 잔액 = 기적립액 + 적립(환입)예정액이
    실제로 닫힌다(농협생명 2026.2Q 해약: 2,314,789 + 31,958 = 2,346,747 / 교보생명
    2026.2Q 대손: 108,269 + (872) = 107,397). `잔액` 행은 이미 합산치이므로 예정액을
    또 더하면 이중계상이다(함정 4).
    잔액 행이 없거나 값이 비면 기적립+예정으로 직접 계산한다 -- 교보생명 2025.3Q 별도가
    그 케이스다(잔액 행 라벨이 오탈자 "해약환금급준비금 잔액"이라 개념 매칭에서 탈락,
    기적립 '-' + 예정 448,503 = 448,503으로 복원).
    """
    s = _scan(ctx, concept)
    bal = _pick(s.get("balance", []))
    if bal is not None:
        v = _val(ctx, bal[1], bal[2])
        if v is not None:
            return abs(v)          # 준비금 stock은 음수 불가 (함정 2)
    acc = _pick(s.get("accrued", []))
    pen = _pick(s.get("pending", []))
    return combine(_val(ctx, acc[1], acc[2]) if acc else None,
                   _val(ctx, pen[1], pen[2]) if pen else None)


def _transposed(ctx: FilingContext) -> list:
    """준비금종류=컬럼 / 값 한 줄=행('이익잉여금')인 뒤집힌 이익잉여금 구성표.

    한화생명 2026.1Q~, 삼성생명 2025.2Q~ 가 이 형태다. 마지막 헤더행이 컬럼명이고
    데이터 행 라벨은 정확히 '이익잉여금'. **이 '이익잉여금' 행 조건이 유일한 안전장치**
    다 -- 삼성생명 2025.4Q 이연법인세표도 마지막 헤더행에 '해약환급금준비금' 컬럼을
    갖고 있어(값 (832,412)) 헤더만 보면 물린다. 그 표의 행 라벨은 '기초 누적일시적차이'
    라 여기서 탈락한다.
    Returns [(tidx, table, {concept: cell})] -- 문서 순서.
    """
    out = []
    for i, t in enumerate(ctx.tables):
        if not t.header:
            continue
        hdr = [norm(c) for c in t.header[-1]]
        idx = {c: hdr.index(c) for c in ITEM_CONCEPTS.values() if c in hdr}
        if not idx:
            continue
        for r in t.rows:
            if r and norm(r[0]) == "이익잉여금":
                out.append((i, t, {c: (r[j] if j < len(r) else None) for c, j in idx.items()}))
                break
    return out


def _ledger(ctx: FilingContext, concept: str) -> list:
    """'이익잉여금의 내역' 표의 맨-개념명 행(= 기적립액). [(tidx, table, row)].

    표 식별은 캡션이 아니라 내용으로 한다: **3셀짜리 '이익준비금' 행이 있는 표**.
    이익잉여금처분계산서도 '1. 이익준비금' 행을 갖지만 그 표의 행은 5셀
    ([과목, 당기값, '', 전기값, ''])이라 3셀 조건에서 탈락한다 -- 처분계산서는 잔액이
    아니라 이번 기 배분이라 기적립액으로 쓰면 안 된다(함정 4, 동양생명 item5 2배 전례).
    """
    cands = []
    for i, t in enumerate(ctx.tables):
        if not any(r and len(r) == 3 and strip_label(r[0]) == "이익준비금" for r in t.rows):
            continue
        for r in t.rows:
            if r and len(r) == 3 and strip_label(r[0]) == concept:
                cands.append((i, t, r))
                break
    return cands


# ---------------------------------------------------------------- KR0104 농협생명
def extract_nh_life(ctx: FilingContext) -> dict[int, float]:
    """농협생명보험 -- P1 표준형, 2023.3Q~2026.2Q 전 분기 동일 형태.

    주석 "(6-1) 해약환급금준비금의 잔액 및 적립예정금액" / "(6-3) 대손준비금의 잔액 및
    환입예정금액" 에 기적립액·예정액·예정잔액 3행이 그대로 있다.
    실측 앵커 2026.2Q: 해약 2,314,789 + 31,958 = 2,346,747 / 대손 14,342 + 0 = 14,342.

    **보증준비금(항목8)은 진짜 0이다** -- 같은 주석이 "(6-2) 보고기간종료일 현재
    보증준비금의 잔액 및 적립예정금액은 없습니다."라고 문장으로 못박고, 이익잉여금 내역표의
    보증준비금 행도 '-'다. 사업의 내용 "가. 준비금 적립내역[K-IFRS 제1104호 기준]" 표에
    보증준비금 48,412가 있지만 그건 **책임준비금(부채) 구성요소**라 이익잉여금 내 법정
    보증준비금과 다른 개념이다 -- 절대 끌어오지 말 것.
    """
    out = {}
    for item, concept in ITEM_CONCEPTS.items():
        v = _from_notes(ctx, concept)
        if v is not None:
            out[item] = v
    return out


# ---------------------------------------------------------------- KR0073 교보생명
def extract_kyobo_life(ctx: FilingContext) -> dict[int, float]:
    """교보생명보험 -- P2 표준형(`...잔액` 행 보유), 2023.1Q~2026.2Q 동일.

    실측 앵커 2026.2Q 별도: 해약 1,255,979 + 1,847,363 = 3,103,342 / 보증 383,236 +
    27,286 = 410,522 / 대손 108,269 + (872) = 107,397.
    해약환급금준비금은 2023.1Q~2025.2Q 전 분기 **진짜 0**이다("당분기말 및 전기말 현재
    해약환급금준비금으로 적립한 내역은 없습니다") -- 2025.3Q에 448,503으로 최초 적립.
    """
    out = {}
    for item, concept in ITEM_CONCEPTS.items():
        v = _from_notes(ctx, concept)
        if v is not None:
            out[item] = v
    return out


# ------------------------------------------------------------- KR0094 신한라이프
def extract_shinhan_life(ctx: FilingContext) -> dict[int, float]:
    """신한라이프생명보험 -- P2 표준형, 2023.3Q~2026.2Q 동일. 연결/별도 값이 동일하다.

    실측 앵커 2026.2Q: 해약 4,918,355 + 730,833 = 5,649,188 / 보증 407,335 + 15,786 =
    423,121 / 대손 6,342 + (50) = 6,292.
    분기별로 실제 움직인다(FY2024 해약 잔액 3,782,633 -> 4,018,556 -> 4,311,838 ->
    3,638,116) -- FY 내 평탄하다고 가정하면 안 된다.
    대손준비금 행 라벨에 각주가 붙는다("대손준비금 환입예정금액(주)") -- `strip_label`이
    꼬리 "(주)"를 벗겨서 접미사 매칭이 살아난다.
    """
    out = {}
    for item, concept in ITEM_CONCEPTS.items():
        v = _from_notes(ctx, concept)
        if v is not None:
            out[item] = v
    return out


# ---------------------------------------------------------------- KR0069 삼성생명
def extract_samsung_life(ctx: FilingContext) -> dict[int, float]:
    """삼성생명보험 -- 연도별로 표 형태가 세 번 바뀐다. 우선순위로 순차 시도한다.

    ① 준비금 주석(P1/P2): 2023.4Q·2024.4Q·2025.4Q(연차보고서에만 있다).
       2025.4Q 별도 앵커: 해약 0 + 832,412 = 832,412 / 대손 335,568 + (36,246) =
       299,322 / 보증 당기표가 통째로 공란(= 미적립).
    ② transposed 이익잉여금 구성표: 2025.2Q~2026.2Q.
       2026.2Q 별도 앵커: 해약 832,412 / 대손 299,321 / 보증 0.
       주의 -- 2025.2Q·3Q 별도표는 보증준비금 컬럼명을 '임의적립금'으로 쓴다(연결표는
       '보증준비금'). 그래서 그 두 분기 항목8은 잡히지 않는데, 같은 시점 실제값이 0이라
       (2024.4Q에 12,297 전액 환입) 결과는 정합적이다.
    ③ 이익잉여금 내역표의 맨-개념명 행(= 기적립액): 2023.3Q·2024.1~3Q·2025.1Q.
       분기보고서에는 예정액 주석이 없어 기적립액이 그 시점 최선의 공시다.

    **해약환급금준비금(항목5)은 2023~2025.3Q 진짜 0이다.** 2023 사업보고서 별도 주석이
    "당기말 및 전기말 현재 해약환급금준비금으로 적립한 내역은 없습니다"라고 명시하고,
    2025.4Q 주석에서 기적립액 0 / 적립예정액 832,412로 처음 등장한다. 억지로 채우지 말 것.
    """
    out = {}
    for item, concept in ITEM_CONCEPTS.items():
        v = _from_notes(ctx, concept)
        if v is None:
            tr = _pick(_transposed(ctx))
            if tr is not None and concept in tr[2]:
                v = _val(ctx, tr[1], [None, tr[2][concept]])
        if v is None:
            led = _pick(_ledger(ctx, concept))
            if led is not None:
                v = _val(ctx, led[1], led[2])
        if v is not None:
            out[item] = abs(v)
    return out


# ---------------------------------------------------------------- KR0068 한화생명
def _is_aggregate_pending(t) -> bool:
    """'감독목적상 적립금 ...' 조정이익표에 준비금 예정액 행이 딱 하나면 그 값은 개별
    개념이 아니라 3종(해약+보증+대손) 합계다 -- 라벨만 대손준비금으로 찍힌다.

    실측: 한화생명 2026.2Q '대손준비금 전입(환입) 예정액 550,860'인데 같은 필링의 대손
    기적립액은 71,219이고, 550,860은 그 표 옆 이익잉여금표의 미처분이익잉여금과 같다
    (421,607 - 550,860 = (129,253) = 그 표의 조정이익, 즉 3종 합계로 계산돼 있다).
    반대로 2023.1Q/3Q/4Q 표의 하단 행은 "**대손준비금** 적립(환입) 후 조정 순이익"이라
    개념이 명시돼 있고 당시엔 이익잉여금 내 준비금이 대손 하나뿐이라 합계=대손이다 --
    그래서 '감독목적상' 문구 유무로 가른다. 2024.4Q·2025.4Q 표는 '감독목적상' 문구를
    쓰지만 3개 개념 행이 모두 있어 개별 귀속이 가능하다.
    """
    labels = [strip_label(r[0]) for r in t.rows if r and r[0]]
    if not any(l.startswith("감독목적상적립금") for l in labels):
        return False
    n = 0
    for l in labels:
        for c in ITEM_CONCEPTS.values():
            if l.startswith(c) and _kind(l[len(c):]) == "pending":
                n += 1
    return n <= 1


def _appropriation(ctx: FilingContext, concept: str) -> list:
    """이익잉여금처분계산서의 'N. <개념>' 행. [(tidx, table, row)].

    보통 처분계산서는 배제 대상(함정 1·4)이지만 한화생명 2023 사업보고서에서는 **여기가
    유일한 정답**이다. 같은 필링의 주석 "(3) 당기 및 전기 중 해약환급금준비금 적립 후
    조정이익" 표는 907,537을 적으면서 각주로 "(*1) 해약환급금준비금 제도의 시행시기는
    당기(2023년)부터이나, 전기초부터 적용을 가정하여, 전기의 해약환급금준비금 전입액을
    산출하였습니다"라고 밝힌다 -- 즉 당기분 pro-forma 증분이지 적립예정액 총액이 아니다.
    처분계산서(raw line 91627-91636)의 '4. 해약환급금준비금 2,504,752,220,405' /
    '5. 보증준비금 183,194,432,055'이 실제 처분액이고, 이 값이 다음 분기(2024.1Q)
    이익잉여금 내역표의 기적립액 2,504,752 / 183,194와 정확히 일치한다.
    2024.4Q·2025.4Q에서는 이 경로와 조정이익표가 같은 값을 준다(1,126,453 / 27,562).
    """
    cands = []
    for i, t in enumerate(ctx.tables):
        if not any(r and r[0] and strip_label(r[0]).startswith("미처분이익잉여금")
                   for r in t.rows):
            continue
        for r in t.rows:
            # 처분계산서 행은 5셀([과목, 당기, '', 전기, '']) -- 3셀 내역표 행과 구분된다.
            if r and len(r) >= 4 and r[0] and strip_label(r[0]) == concept:
                cands.append((i, t, r))
                break
    return cands


def extract_hanwha_life(ctx: FilingContext) -> dict[int, float]:
    """한화생명 -- 5사 중 가장 험한 필링. 연결 주석엔 준비금 내역표가 없어 블록은 하나다.

    기적립액 소스가 연도마다 다르다:
      ③ 이익잉여금 내역표(3셀 행)  : 2023.1Q~2025.1Q
      ② '<개념> 기적립액' 단일컬럼표 : 2025.2Q~2025.4Q
      ① transposed 구성표          : 2026.1Q~2026.2Q
    예정액은 연차보고서에만 있고(분기엔 3종 합계 한 줄뿐 -- `_is_aggregate_pending` 참조)
    처분계산서 > 조정이익표 순으로 잡는다.

    검산 (기적립액 + 예정액 = 다음 분기 기적립액):
      2023.4Q 해약 0 + 2,504,752 = 2,504,752  -> 2024.1Q 기적립액 2,504,752 ✔
      2023.4Q 보증 0 +   183,194 =   183,194  -> 2024.1Q 기적립액   183,194 ✔
      2023.4Q 대손 181,703 + (80,372) = 101,331 -> 2024.1Q 101,331 ✔
      2024.4Q 해약 2,504,752 + 1,126,453 = 3,631,205 -> 2025.1Q 3,631,206 ✔(반올림 1)
      2025.4Q 해약 3,631,206 + 2,876,584 = 6,507,790 -> 2026.1Q 6,507,790 ✔
    2026.2Q 값: 해약 6,507,790 / 대손 71,219 / 보증 237,210 (transposed 당반기말 표).
    """
    out = {}
    for item, concept in ITEM_CONCEPTS.items():
        acc = pen = None
        # --- 기적립액 ---
        tr = _pick(_transposed(ctx))
        if tr is not None and concept in tr[2]:
            acc = _val(ctx, tr[1], [None, tr[2][concept]])
        if acc is None:
            hit = _pick(_scan(ctx, concept).get("accrued", []))
            if hit is not None:
                acc = _val(ctx, hit[1], hit[2])
        if acc is None:
            led = _pick(_ledger(ctx, concept))
            if led is not None:
                acc = _val(ctx, led[1], led[2])
        # --- 적립(환입)예정액 ---
        # 처분계산서 경로는 해약/보증 전용이다. 대손준비금은 처분계산서에서 "II. 이익잉여금
        # 이입액" 아래에 **양수 환입액**으로 실려(2023: 80,372) 부호가 반대인데, 같은
        # 필링의 조정이익표는 (80,372)으로 부호까지 맞게 적어 준다 -- 그래서 대손은
        # 조정이익표만 쓴다.
        if concept in ("해약환급금준비금", "보증준비금"):
            ap = _pick(_appropriation(ctx, concept))
            if ap is not None:
                pen = _val(ctx, ap[1], ap[2])
        if pen is None:
            hit = _pick(_scan(ctx, concept).get("pending", []))
            if hit is not None and not _is_aggregate_pending(hit[1]):
                pen = _val(ctx, hit[1], hit[2])
        v = combine(acc, pen)
        if v is not None:
            out[item] = v
    return out


HANDLERS = {
    "KR0068": extract_hanwha_life,
    "KR0069": extract_samsung_life,
    "KR0073": extract_kyobo_life,
    "KR0094": extract_shinhan_life,
    "KR0104": extract_nh_life,
}
