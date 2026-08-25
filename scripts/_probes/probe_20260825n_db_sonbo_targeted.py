# -*- coding: utf-8 -*-
"""DB손해보험 2023.2Q raw, offset ~60277 근방(보험서비스결과=971,297,908,122 나오는 표)의
넓은 컨텍스트만 정확히 뽑는다 (read-only)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

d = ROOT / "data/dart/FY2023_Q2/raw/KR0011_DB손해보험"
for x in sorted(d.glob("*.xml")):
    raw = x.read_bytes()
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        t = raw.decode("cp949", errors="replace")
    t2 = re.sub(r"<[^>]+>", " ", t)
    t2 = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", t2)
    t2 = re.sub(r"\s+", " ", t2)
    i = t2.find("971,297,908,122")
    if i == -1:
        continue
    print(f"[{x.name}] found at {i}")
    print(t2[max(0, i - 1800): i + 1200])
