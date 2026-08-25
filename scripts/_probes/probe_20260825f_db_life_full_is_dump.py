# -*- coding: utf-8 -*-
"""디비생명보험(KR0082) 2023.1Q raw '(2) 요약포괄손익계산서' 전체를 덤프해 영업이익까지의
전 라인(투자손익/보험금융손익 유무, 재보험손익 위치)을 직접 확인한다 (read-only)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

d = sorted((ROOT / "data/dart/FY2023_Q1/raw").glob("KR0082_*"))[0]
for x in sorted(d.glob("*.xml")):
    raw = x.read_bytes()
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        t = raw.decode("cp949", errors="replace")
    t2 = re.sub(r"<[^>]+>", " ", t)
    t2 = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", t2)
    t2 = re.sub(r"\s+", " ", t2)
    i = t2.find("요약포괄손익계산서")
    while i != -1:
        print(f"=== [{x.name}] offset {i} ===")
        print(t2[i:i + 1800])
        print()
        i = t2.find("요약포괄손익계산서", i + 1)
