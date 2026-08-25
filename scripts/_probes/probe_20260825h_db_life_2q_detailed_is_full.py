# -*- coding: utf-8 -*-
"""KR0082 2023.2Q raw 별도 '(2) 요약포괄손익계산서'(원 단위) I.보험서비스손익~영업이익
전체 라인 덤프 (read-only)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

d = sorted((ROOT / "data/dart/FY2023_Q2/raw").glob("KR0082_*"))[0]
for x in sorted(d.glob("*.xml")):
    raw = x.read_bytes()
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        t = raw.decode("cp949", errors="replace")
    t2 = re.sub(r"<[^>]+>", " ", t)
    t2 = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", t2)
    t2 = re.sub(r"\s+", " ", t2)
    i = t2.find("I. 보험서비스손익")
    while i != -1:
        print(f"=== [{x.name}] offset {i} ===")
        print(t2[i:i + 2600])
        print()
        i = t2.find("I. 보험서비스손익", i + 1)
