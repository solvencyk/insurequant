#!/usr/bin/env python3
"""정기경영공시 raw PDF 의 디스크 위치를 푸는 단일 헬퍼.

**왜 있나 (2026-09-01).** 이 저장소는 13분기 동안 `data/disclosure/<period>/raw/` 에 회사별
PDF 를 떨궈 왔는데, **2026.2Q 부터 다운로더가 `<period>/pdf/` 로 바꿨다**(`src/solvency/config.py`
의 `disclosure_pdf_path()` 가 원래 선언한 정본 위치가 `pdf/` 다 — 즉 13분기 쪽이 관행이었고
2026.2Q 가 선언과 맞다). 실측 census:

    FY2023_Q1..FY2026_Q1   raw=38~40   pdf=0
    FY2026_Q1              raw=39      pdf=1
    FY2026_Q2              raw=1       pdf=39      <- 뒤집혔다

`raw/` 만 glob 하는 코드는 **2026.2Q 39사를 조용히 스킵한다.** 예외도 로그도 안 남기고
"원천이 없다" 로 흘러가 게이트에서 `UNMEASURED`/`NO_RAW_PDF` 로 찍힌다 —
`값이 틀리다` 가 아니라 `판정 근거가 통째로 비었다` 라서 눈에 안 띈다. 이 저장소에서 같은
버그가 최소 세 번 났다:

  1. `scripts/rebuild_combined_transition_after.py::_pdf()`  (수정됨)
  2. `scripts/fill_market_subitems_to_disclosure.py`         (수정됨, raw-first 폴백)
  3. `scripts/build_kics_source_textlayer.py` +
     `scripts/extract_transition_applicability.py::pdf_fallback` +
     `scripts/validate_kics_disclosure.py::_source_readability` (2026-09-01, 이 모듈로 수정)

**탐색 순서는 raw/ 우선, 없을 때만 pdf/ 다.** 과거 13분기의 해석을 한 칸도 바꾸지 않기 위한
것이다(raw/ 에 매치가 있으면 pdf/ 는 아예 안 본다). 새 분기처럼 raw/ 가 비어 있을 때만
pdf/ 로 떨어진다.

이 모듈은 stdlib 만 쓰고 부작용이 없다 — 게이트에서 import 해도 안전하다.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCLOSURE = ROOT / "data" / "disclosure"

# 탐색 순서. raw/ 가 먼저인 것이 계약이다 — 뒤집으면 과거 분기 해석이 바뀐다.
SUBDIRS = ("raw", "pdf")


def period_of(quarter: str) -> str:
    """'2026.2Q' -> 'FY2026_Q2'."""
    return f"FY{quarter[:4]}_Q{quarter[5]}"


def disclosure_pdfs(period: str, code: str, root: Path | None = None) -> list[Path]:
    """(period, 회사코드) -> 매칭되는 PDF 목록. raw/ 에 있으면 그것만, 없으면 pdf/ 를 본다.

    period 는 'FY2026_Q2' 형식. code 는 'KR0069' 같은 회사코드.
    반환은 정렬된 리스트이며, 못 찾으면 빈 리스트다.
    """
    base = (root or DISCLOSURE)
    for sub in SUBDIRS:
        d = base / period / sub
        if not d.is_dir():
            continue
        hits = sorted(d.glob(f"{code}_*.pdf"))
        if hits:
            return hits
    return []


def disclosure_pdf_dirs(period: str, root: Path | None = None) -> list[Path]:
    """(period) -> 존재하는 PDF 디렉토리들. raw/ 먼저, 그다음 pdf/."""
    base = (root or DISCLOSURE)
    return [base / period / sub for sub in SUBDIRS if (base / period / sub).is_dir()]


def find_disclosure_pdf(period: str, filename: str, root: Path | None = None) -> Path | None:
    """이미 알고 있는 파일명을 raw/ · pdf/ 어느 쪽에 있든 찾아 준다.

    사이드카가 기록한 파일명을 디스크와 대조(freshness 검사)할 때 쓴다 — 한쪽 디렉토리만
    보면 파일이 멀쩡히 있는데도 'stale' 로 강등되어 그 칸이 통째로 판정 불가가 된다.
    """
    base = (root or DISCLOSURE)
    for sub in SUBDIRS:
        p = base / period / sub / filename
        if p.exists():
            return p
    return None
