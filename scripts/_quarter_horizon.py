#!/usr/bin/env python3
"""분기 지평(quarter horizon) 단일 정본 — **마스터에서 파생한다. 손으로 늘리지 않는다.**

왜 있나 (2026-08-29, `inbox/validation/20260829T1910Z`)
------------------------------------------------------
게이트 세 개가 각자 자기 분기 목록을 **리터럴로** 들고 있었고, 셋 다 `2026.1Q` 에서
끝나 있었다:

    scripts/validate_master_tables.py        QS                (최초 커밋 9243445부터)
    scripts/validate_data_contract.py        _DISPLAY_QUARTERS  (+ 죽은 QS 리터럴)
    scripts/validate_kics_rate_sensitivity.py ALL_Q

그 결과 2026.2Q 를 라이브에 배포한 날, coverage census · qoq · spike · wfy · continuity 가
**그 분기를 한 번도 순회하지 않았다.** 게이트가 찍은 `RED=0` 은 그 분기에 대해서는
"검사했더니 깨끗"이 아니라 **"안 봤다"** 였다. 실측(같은 티켓): 지평에 2026.2Q 를 넣자
`HOLE-PL 흥국화재 2026.2Q` 가 즉시 드러났고(항목 2/8/12/13/14 결측, 직전 2026.1Q 는 전부
정상 → 최신 분기 회귀), `validate_data_contract` 의 `MASTER_HOLE` RED 로 승격됐다.

**하드코딩 자체가 재발 구조다.** 분기가 늘 때마다 사람이 세 곳을 고쳐야 하면 다음에 또
빠진다 — 실제로 `validate_data_contract` 안의 두 검사(배당·CSM 연속성)는 주석에
"`_DISPLAY_QUARTERS` 는 2026.2Q 를 아직 포함하지 않는다"고 적어 놓고 **자기만 스코프를
비켜갔다.** 알고도 정본을 안 고친 것이다.

파생 규칙
---------
* **하한은 고정** (`QUARTER_FLOOR = 2023.1Q`) — K-ICS/IFRS17 공시 개시 분기. 데이터에서
  파생하면 IFRS17_BS 의 2021.4Q 까지 끌려와 없는 분기가 통째로 hole 이 된다.
* **상한은 저장소 전체 마스터의 high-water mark.** 한 마스터에서만 파생하면 그 마스터가
  최신 분기를 통째로 빠뜨렸을 때 지평도 같이 줄어 **결측이 보이지 않는다**(자기참조 사각).
  여러 마스터의 max 를 쓰면 다른 마스터가 그 분기를 갖고 있는 한 지평이 남고, 빈 쪽이
  hole 로 찍힌다.
* 값은 `공시분기` 필드에서만 읽는다. 파일 전체를 정규식으로 훑으면 `비고`·주석 필드의
  산문에 적힌 분기까지 주워 지평이 허수로 늘어난다.

이 규칙이 실제로 지켜지는지는 `tests/test_quarter_horizon.py` 가 강제한다(게이트가 자기
분기 리터럴을 다시 심으면 거기서 막힌다).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

QUARTER_FLOOR = "2023.1Q"

# high-water mark 를 세는 마스터. 한 개가 최신 분기를 빠뜨려도 나머지가 지평을 지킨다.
HORIZON_SOURCES = (
    "PL_breakdown.json",
    "CSM_waterfall.json",
    "IFRS17_BS.json",
    "kics_disclosure.json",
    "dividend.json",
)

# `"공시분기": "2026.2Q"` 만 잡는다 (산문 안의 분기 언급은 제외).
_QRE = re.compile(rb'"\xea\xb3\xb5\xec\x8b\x9c\xeb\xb6\x84\xea\xb8\xb0"\s*:\s*"(20\d\d\.[1-4]Q)"')


def _key(q: str) -> tuple[int, int]:
    return int(q[:4]), int(q[5])


def quarter_range(lo: str, hi: str) -> list[str]:
    """'2023.1Q','2026.2Q' -> 연속 분기 목록. hi < lo 면 [lo]."""
    y, n = _key(lo)
    ey, en = _key(hi)
    out = [lo]
    while (y, n) < (ey, en):
        y, n = (y + 1, 1) if n == 4 else (y, n + 1)
        out.append(f"{y}.{n}Q")
    return out


def latest_quarter(sources=HORIZON_SOURCES, floor: str = QUARTER_FLOOR) -> str:
    """마스터들의 `공시분기` 최댓값. 파일이 하나도 없으면 floor (slim 워크트리)."""
    top = floor
    for name in sources:
        p = ROOT / name
        if not p.exists():
            continue
        found = _QRE.findall(p.read_bytes())
        if found:
            best = max(q.decode() for q in found)
            if _key(best) > _key(top):
                top = best
    return top


def quarter_horizon(floor: str = QUARTER_FLOOR) -> list[str]:
    """검증이 순회해야 하는 전체 분기 목록 (floor .. 최신)."""
    return quarter_range(floor, latest_quarter(floor=floor))


def display_quarters(floor: str = QUARTER_FLOOR) -> set[str]:
    """사이트가 그리는 분기 = RED 스코프 (owner 2026-06-20).

    원래 리터럴은 {2023.4Q, 2024.4Q, 2025.1Q~2026.1Q} 7개였다. 그 집합의 규칙은
    **연말(4Q) 전부 + 2025.1Q 이후 전부** 이고, 여기서 그 규칙을 그대로 파생한다
    (같은 지평에서 돌리면 종전 7개를 정확히 재현하고, 최신 분기만 자동으로 붙는다).
    중간분기(2023.1~3Q / 2024.1~3Q)는 사이트 비노출 + raw git-purge 라 스코프 밖이다.
    """
    return {q for q in quarter_horizon(floor) if q.endswith(".4Q") or q >= "2025.1Q"}


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    qs = quarter_horizon()
    print(f"latest       = {latest_quarter()}")
    print(f"horizon (n={len(qs)}) = {qs[0]} .. {qs[-1]}")
    print(f"display      = {sorted(display_quarters())}")
