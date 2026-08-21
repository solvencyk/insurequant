#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""법정준비금(항목5·6·7·8) 회사별 본문-XML 추출 -- 디스패치.

`build_ifrs17_bs.py`가 FS API로 못 채운 (회사, 분기) 칸에 대해 이 패키지를 호출한다.
계약과 함정은 `common.py` docstring 참조. 회사별 핸들러는 그룹 모듈에 있고,
각 모듈의 `HANDLERS` dict가 여기로 합쳐진다 -- **등록 안 된 함수는 죽은 코드다.**
"""
from __future__ import annotations

from pathlib import Path

from scripts.reserve_extract.common import FilingContext, load  # re-export

_MODULES = ("life_major", "life_mid", "life_small", "tier2_audit",
            "nonlife_small", "misc_remaining", "nonlife_major")
HANDLERS: dict[str, object] = {}

for _name in _MODULES:
    try:
        _mod = __import__(f"scripts.reserve_extract.{_name}", fromlist=["HANDLERS"])
    except ImportError:
        continue  # 아직 안 만들어진 그룹 모듈은 조용히 건너뛴다 (점진 온보딩)
    _dup = set(getattr(_mod, "HANDLERS", {})) & set(HANDLERS)
    if _dup:
        raise RuntimeError(f"중복 등록된 회사코드 {sorted(_dup)} -- {_name}과 다른 모듈이 충돌")
    HANDLERS.update(getattr(_mod, "HANDLERS", {}))


def extract(kr: str, xml_path: Path) -> dict[int, float]:
    """{5:.., 6:.., 7:.., 8:..} (아는 항목만). 핸들러 없으면 빈 dict."""
    fn = HANDLERS.get(kr)
    if fn is None:
        return {}
    try:
        return fn(load(xml_path)) or {}
    except Exception:
        return {}
