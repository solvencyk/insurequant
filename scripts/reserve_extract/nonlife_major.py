#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""법정준비금 회사별 추출 -- 대형 손해보험사.

`_MODULES` 에 이름만 있고 파일이 없던 그룹이다(디스패치가 ImportError 를 조용히 넘겨
점진 온보딩하는 구조). 2026-08-20 에 삼성화재로 개시했다 --
발주: `inbox/parser/20260820T1900Z` (validation, 뒤채움 과대계상).

## 왜 전용 핸들러가 필요한가 -- 괄호 주기형(parenthetical) 표기

삼성화재는 2023년 상반기 필링에서 **해약환급금준비금을 표의 행으로 싣지 않고 요약재무정보
이익잉여금 행의 괄호 주기로만** 공시한다:

```
V. 이익잉여금(주석30) (대손준비금 환입예정액: 44,832,833,355 원  기적립액: 247,412,854,764 원)
                     (비상위험준비금 적립예정액: 12,092,188,652 원  기적립액 : 2,572,265,386,862 원)
                     (해약환급금준비금 적립예정액: 556,503,490,830 원)
```

범용 추출기(`parse_filing`)는 **표의 행 라벨**로 개념을 찾으므로 이 형태에 닿지 못한다.
그래서 2023.1Q·2023.2Q 해약환급금준비금이 결측이 됐고, 그 자리에 2023.3Q 값 916,764 이
뒤로 복사돼 **공시값 556,503 의 1.65배**가 마스터에 실려 있었다.

전 저장소 366 필링을 이 정규식으로 스캔한 결과 이 표기를 쓰는 (회사, 분기)는 **삼성화재
2023.1Q·2023.2Q 두 칸뿐**이다 -- 범용 경로에 넣지 않고 회사 핸들러로 좁게 다루는 이유다.

## 함정

- **단위가 `원`이다**(표의 백만원과 다름). 괄호 안 숫자는 항상 `원` 단위로 찍힌다.
- **연결/별도 두 벌이 나온다.** 이 마스터는 OFS(별도) 고정이므로 별도 블록을 써야 한다.
  삼성화재 2023.1Q·2Q 는 두 값이 **동일**해 실질 차이가 없지만(실측), 다른 회사가 이
  경로를 타게 되면 반드시 확인해야 한다. 여기서는 같은 개념에 서로 다른 값이 나오면
  그 개념을 **버린다**(추측해 고르지 않는다).
- **기적립액이 없는 것은 결측이 아니다.** 해약환급금준비금은 2023년 신설 제도라 그 해
  상반기에는 기적립 잔액이 존재하지 않는다 -- `적립예정액` 단독이 곧 그 시점의 적립액이다.
  FS-API 로 확증됨(2026-08-20): 삼성화재·현대해상 둘 다 2023년 전 분기에서
  `dart_SurrenderValueReserve`(기적립액) = **0**, `...ToBeAdded`(적립예정액)만 값이 있다.

- 🔴 **다른 회사에 이 경로를 그대로 확대하지 마라 -- 회사마다 괄호가 담는 게 다르다.**
  현대해상 2023.1Q 필링은 같은 이익잉여금 괄호에
  `해약환급금준비금 적립예정금액 당 1분기: 352,470,800,897원`(=352,471) 을 쓰는데,
  같은 필링의 P1 표와 FS-API 는 **4,391,552** 다(12.5배 차이). 즉 그 회사 괄호의 숫자는
  이 마스터의 item5 정의가 **아니다**. 삼성화재 괄호는 정의와 맞고(2023 시계열
  259,134 → 556,503 → 916,764 → 1,180,012 이 매끄럽게 이어지며 뒤 두 개는 FS-API 확인분),
  현대해상 괄호는 안 맞는다. 지금은 `HANDLERS` 가 KR0008 하나뿐이라 안전하지만,
  회사를 추가할 때는 **그 회사 FS-API 값과 먼저 대조**하고 넣어라.
"""
from __future__ import annotations

import re

from scripts.reserve_extract.common import FilingContext, ITEM_CONCEPTS, combine

# `(<개념> <종류>: 1,234,567 원)` -- 콜론 앞뒤 공백과 전각 콜론, `기적립액 :` 처럼 벌어진
# 공백까지 허용한다(원문에 실제로 둘 다 나온다).
_PAREN = re.compile(
    r"(해약환급금준비금|비상위험준비금|대손준비금|보증준비금)\s*"
    r"(적립예정액|환입예정액|적립\(환입\)예정액|추가적립예정액|기적립액)\s*[:：]\s*"
    r"([0-9][0-9,]*)\s*원")
_PENDING_KINDS = ("적립예정액", "환입예정액", "적립(환입)예정액", "추가적립예정액")


def _paren_amounts(ctx: FilingContext) -> dict[str, dict[str, float]]:
    """{개념: {종류: 백만원}}. 같은 (개념, 종류)에 서로 다른 값이 나오면 그 키를 버린다."""
    seen: dict[tuple[str, str], set[float]] = {}
    for m in _PAREN.finditer(ctx.xml_path.read_text(encoding="utf-8", errors="replace")):
        concept, kind, num = m.group(1), m.group(2), m.group(3)
        seen.setdefault((concept, kind), set()).add(float(num.replace(",", "")) / 1e6)
    out: dict[str, dict[str, float]] = {}
    for (concept, kind), vals in seen.items():
        if len(vals) != 1:          # 연결≠별도 -- 어느 쪽인지 못 가리면 안 쓴다
            continue
        out.setdefault(concept, {})[kind] = vals.pop()
    return out


# **항목5만** 돌려준다. 같은 괄호에 비상위험·대손도 실려 있지만 그 둘은 이 회사의 이익잉여금
# 구성내역 **표에 행으로도** 있어서 범용 추출기가 이미 제대로 잡는다(실측 2023.2Q: 비상위험
# 2,572,265 · 대손 247,413). 핸들러는 1순위라 여기서 같이 돌려주면 그 정상값을 괄호 일부만
# 읽은 값으로 덮어쓴다 -- 실제로 처음 그렇게 짰다가 비상위험이 2,572,265 -> 12,092 로
# 망가지는 것을 확인하고 좁혔다. 표에 행이 아예 없는 해약환급금준비금만 이 경로가 필요하다.
_HANDLED_ITEMS = (5,)


def extract_samsung_fire(ctx: FilingContext) -> dict[int, float]:
    """삼성화재해상보험 (KR0008). 괄호 주기형이 없는 분기는 빈 dict -- 그 분기는 범용
    추출기/FS-API 가 이미 처리하고 있으므로 여기서 손대지 않는다."""
    paren = _paren_amounts(ctx)
    if not paren:
        return {}
    out: dict[int, float] = {}
    for item in _HANDLED_ITEMS:
        kinds = paren.get(ITEM_CONCEPTS[item])
        if not kinds:
            continue
        pending = next((kinds[k] for k in _PENDING_KINDS if k in kinds), None)
        v = combine(kinds.get("기적립액"), pending)
        if v is not None:
            out[item] = v
    return out


HANDLERS = {"KR0008": extract_samsung_fire}
