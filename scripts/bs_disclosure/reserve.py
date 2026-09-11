# -*- coding: utf-8 -*-
"""법정준비금 5/6/7/8 -- 새로 구현하지 않고 이미 39사 전수검증을 거친
scripts/_probes/probe_20260902_surrender_reserve_vs_disclosure.py 를 그대로 재사용한다
(2026-09-02~03, 84th/85th pass -- P1~P5 우선순위·각주 문장 파싱·별도/연결 판별까지 이미
확정돼 있다). 여기서는 그 모듈의 `parse_pdf()` 를 임포트해 얇게 감싸기만 한다."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_PROBE_PATH = ROOT / "scripts" / "_probes" / "probe_20260902_surrender_reserve_vs_disclosure.py"

_spec = importlib.util.spec_from_file_location("_reserve_probe_2026911", _PROBE_PATH)
_reserve_probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reserve_probe)  # type: ignore[union-attr]

parse_pdf = _reserve_probe.parse_pdf
ITEM_REPORT_NAME = _reserve_probe.ITEM_REPORT_NAME
P_LOW = _reserve_probe.P_LOW


def extract_reserves(pdf_path: Path) -> tuple[dict[int, float], dict[int, str]]:
    """(값 dict, skip_reason dict). 값은 이미 백만원(모듈 내부에서 단위 환산까지 끝낸다)."""
    result = parse_pdf(pdf_path)
    if not result:
        return {}, {}
    values: dict[int, float] = {}
    skips: dict[int, str] = {}
    for item, (best, distinct_vals) in result.items():
        if len(distinct_vals) > 1:
            skips[item] = f"발행사 자기모순(같은 우선순위에서 값이 갈림): {sorted(distinct_vals)}"
            continue
        prio, val, unit, hdr, label, method, page_no, _is_consol = best[0]
        if prio == P_LOW and unit is None:
            skips[item] = "단위 불명(저신뢰, P_LOW) -- 스킵"
            continue
        values[item] = 0.0 if val == "none" else val
    return values, skips
