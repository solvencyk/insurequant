#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""법정준비금(항목5·6·7·8) 회사별 본문-XML 추출 -- 공용 헬퍼.

**왜 이 패키지가 생겼나 (owner 2026-08-19, inbox/parser/20260819T0500Z):**
FS API가 법정준비금 4종을 `기적립액`/`적립(환입)예정액` 두 태그로 나눠 내는데,
`build_ifrs17_bs.py::ACCOUNT_IDS`가 앞쪽만 읽어서 값이 항상 예정액만큼 모자랐다. 그 상수는
고쳤지만(PENDING_ACCOUNT_IDS), **API에 재무제표 자체가 없거나 준비금을 태그 안 하는 27개사**는
본문 XML에서 긁어야 한다. 그 회사별 핸들러가 이 패키지에 산다.

```
적립액 = 기적립액 + 적립(환입)예정액     (owner 확정 공식)
```

## 계약 (핸들러 작성자는 이것만 지키면 된다)

```python
def extract_<company>(ctx: FilingContext) -> dict[int, float]:
    # returns {5: 해약환급금적립액, 6: 비상위험, 7: 대손, 8: 보증} -- 아는 항목만
```

값은 **백만원 단위 최종 적립액**(기적립+예정 합산 후)으로 돌려준다. 못 찾은 항목은 키를 빼라
(0을 넣지 마라 -- 진짜 0과 미공시가 구분돼야 한다).

핸들러를 만들었으면 그 모듈의 `HANDLERS` dict에 `"KR00XX": extract_<company>`로 **등록**해야
살아난다(등록 안 하면 죽은 코드 -- PL breakdown에서 실제로 그런 전례가 있다).

## 함정 (전부 실측으로 확인된 것들)

1. **시그니처 함정** -- 행 라벨이 `해약환급금준비금`+`비상위험/대손`인 표만 보고 뽑으면
   이연법인세표·이익잉여금 내역표·조정이익표까지 물린다(DB손보 △2,645,780 등 음수 오탐).
   `is_excluded_caption()`으로 걸러라.
2. **준비금 stock은 음수 불가.** 표 프레이밍(조정이익/처분계산서/준비금주석)마다 부호가
   뒤집혀 나오므로 최종값은 `abs()`가 안전하다(진짜 환입은 전분기 대비 감소로 나타난다).
3. **lxml sourceline 65535 캡.** 대형 필링(한화생명 등 6.5만줄 초과)에서는 `find_unit()`의
   위치기반 단위판정이 무의미해진다. `scale_guard()`를 반드시 통과시켜라.
4. **중복 계상.** 한 필링 안에 같은 개념이 3~5개 표에 다른 부호·범위로 나온다. 처분계산서의
   `...전입액`과 이익잉여금 내역표의 `...준비금`이 같은 사건인 경우가 흔하다 -- 한 회사에서
   후보가 여럿이면 **표를 골라라**(합치지 마라).
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context

UNIT_SCALE = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0, "천 원": 1e-3, "백만 원": 1.0,
              "십억원": 1e3, "억원": 1e2}

# 이 단어가 캡션에 있으면 그 표는 준비금 잔액표가 아니다 (owner 확정 목록 + 실측 추가).
EXCLUDED_CAPTION_WORDS = ("이연법인세", "일시적차이", "조정이익", "조정손익", "순이익",
                          "주당", "처분계산서", "자본변동", "현금흐름")

ITEM_CONCEPTS = {5: "해약환급금준비금", 6: "비상위험준비금", 7: "대손준비금", 8: "보증준비금"}


def norm(s: str | None) -> str:
    """공백 전부 제거 (전각 공백·개행 포함)."""
    return re.sub(r"\s+", "", (s or "").replace("　", " "))


def strip_label(s: str | None) -> str:
    """행 라벨에서 선행 번호/로마숫자/글머리와 후행 각주표시를 벗긴다.

    실측 대응: "4. 해약환급금준비금 전입액"(하나생명) / "해약환급금준비금(*)"(DB생명) /
    "Ⅳ. 기타포괄손익누계액(주석23)"(아이엠라이프) / "3. 해약환급금준비금"(동양생명).
    """
    lab = norm(s)
    lab = re.sub(r"^[IVXⅠ-Ⅹ]+[.\s]*", "", lab)
    lab = lab.lstrip("ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ.0123456789()가나다라마바사아자차")
    lab = re.sub(r"\(\*+\d*\)$", "", lab)
    lab = re.sub(r"\(주\d*\)$", "", lab)
    lab = re.sub(r"\(주석[^)]*\)$", "", lab)
    return lab


def num(s: str | None) -> float | None:
    """'1,633,087' / '(2,913)' / '△557' / '-' -> float | None."""
    if s is None:
        return None
    s = norm(s).replace(",", "")
    if not s or s in ("-", "―", "－", "0"):
        return 0.0 if s == "0" else None
    neg = (s.startswith("(") and s.endswith(")")) or s.startswith("△") or s.startswith("-")
    s = s.strip("()").lstrip("△-")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def is_excluded_caption(caption: str | None) -> bool:
    """준비금 잔액표가 아닌 표(함정 1)인지."""
    c = norm(caption)
    return any(w in c for w in EXCLUDED_CAPTION_WORDS)


@dataclass
class FilingContext:
    """한 필링(XML 한 개)에 대한 파싱 컨텍스트. 핸들러가 받는 유일한 인자."""
    xml_path: Path
    tables: list          # list[ExtractedTable] -- .caption / .header / .rows / .line_no
    unit_markers: list    # [(line_no, scale), ...] 오름차순

    def find_unit(self, line_no: int) -> float:
        """line_no 이전 마지막 '단위:X' 마커의 스케일. 없으면 원(1e-6) 기본."""
        scale = 1e-6
        for ln, sc in self.unit_markers:
            if ln > line_no:
                break
            scale = sc
        return scale

    def rows_matching(self, *, concept: str | None = None, exact: str | None = None,
                      contains: str | None = None, allow_excluded: bool = False):
        """조건에 맞는 (table, row, stripped_label) 을 순회. 캡션 함정은 기본 배제."""
        for t in self.tables:
            if not allow_excluded and is_excluded_caption(t.caption):
                continue
            for r in t.rows:
                if not r or not r[0]:
                    continue
                lab = strip_label(r[0])
                if exact is not None and lab != exact:
                    continue
                if contains is not None and contains not in lab:
                    continue
                if concept is not None and not lab.startswith(concept):
                    continue
                yield t, r, lab


def load(xml_path: Path) -> FilingContext:
    """XML 하나를 파싱해 FilingContext로. 단위마커는 원문 텍스트에서 직접 스캔한다
    (표의 .caption은 앞쪽 무관한 문단을 잘못 붙잡는 경우가 흔해 신뢰할 수 없다)."""
    lines = xml_path.read_text(encoding="utf-8", errors="replace").split("\n")
    markers = []
    for i, line in enumerate(lines, start=1):
        for m in re.finditer(r"단위\s*[:：]\s*([가-힣]+)", line):
            if m.group(1) in UNIT_SCALE:
                markers.append((i, UNIT_SCALE[m.group(1)]))
    return FilingContext(xml_path=xml_path, tables=list(_iter_tables_with_context(xml_path)),
                         unit_markers=markers)


def scale_guard(raw_value: float, scale: float, line_no: int = 0) -> float:
    """단위 적용 + 매그니튜드 안전장치 (함정 3).

    lxml `.sourceline`은 부호없는 16비트라 65535에서 캡되고, 그 이상 줄수의 필링에서는
    `find_unit()`의 위치기반 판정이 통째로 무의미해진다. 실측 2건 -- 방향이 서로 반대:
      (a) 한화생명 FY2023 보증준비금: 원표 183,194,432,055원인데 scale=1.0(백만원 오판)
          -> 그대로 찍혀 1e6배 과다 (실제 183,194백만원)
      (b) 한화생명 FY2024.1Q 해약환급금: 원표 2,504,752(이미 백만원 인쇄)인데 scale=1e-6
          (원 오판) -> 2.504752로 찍혀 1e6배 과소 (화면엔 "3"으로 반올림돼 보임)
    캡에 안 걸린 표는 위치판정을 그대로 신뢰한다(방어를 걸면 진짜 소액을 오판할 위험).
    """
    out = raw_value * scale
    if line_no < 65535:
        return out
    if abs(out) > 1e8:              # >10만조원, 어떤 회사도 불가능
        return raw_value * scale * 1e-6
    if abs(out) < 100 and abs(raw_value) >= 1000:   # <1억원인데 원표는 4자리 이상
        return raw_value * scale * 1e6
    return out


def combine(accrued: float | None, pending: float | None) -> float | None:
    """owner 확정 공식: 적립액 = 기적립액 + 적립(환입)예정액.

    준비금 stock은 음수가 될 수 없으므로(함정 2) 최종값은 절댓값을 취한다 -- 표 프레이밍마다
    부호가 뒤집혀 나오는데 그걸 행 단위로 맞히려는 시도는 실측에서 두 번 실패했다
    (한화생명 양수 / 흥국생명 괄호음수, 같은 라벨·같은 표 형태·같은 방향 사건).
    둘 다 None이면 None(미공시), 하나만 있으면 그것만.
    """
    if accrued is None and pending is None:
        return None
    return abs((accrued or 0.0) + (pending or 0.0))
