# -*- coding: utf-8 -*-
"""디비생명보험(KR0082) 2023.1Q/2023.2Q raw 요약포괄손익계산서 직접 재현 (read-only).

inbox/parser/20260825T1120Z iter2 §3: validation 이 확인한 부모행(I. 보험서비스손익) vs
자식행(1. 보험손익) 오선택을 raw XML에서 독립적으로 재확인하고, 같은 병이 2023.2Q(validation
평가 범위 밖, item16 결측으로 미검증)에도 있는지 함께 확인한다.

usage:
    python scripts/_probes/probe_20260825c_db_life_parent_row_check.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")


def strip_xml(path: Path) -> str:
    raw = path.read_bytes()
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        t = raw.decode("cp949", errors="replace")
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", t)
    return re.sub(r"\s+", " ", t)


def dump(fy_q: str):
    d = sorted((ROOT / "data" / "dart" / fy_q / "raw").glob("KR0082_*"))
    if not d:
        print(f"{fy_q}: no raw dir")
        return
    rd = d[0]
    print(f"=== {fy_q}  dir={rd.name} ===")
    for x in sorted(rd.glob("*.xml")):
        txt = strip_xml(x)
        for m in re.finditer(r"보험서비스손익", txt):
            ctx = txt[max(0, m.start() - 90): m.start() + 220]
            print(f"  [{x.name}] ...{ctx}...")
        print()


for q in ("FY2023_Q1", "FY2023_Q2"):
    dump(q)
