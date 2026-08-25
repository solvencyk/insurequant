# -*- coding: utf-8 -*-
"""DB손해보험(KR0011) 2023.2Q raw 요약재무정보/영업이익 주변 컨텍스트 (read-only)."""
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
    print(f"=== [{x.name}] 요약재무정보 @49888 ===")
    print(t2[49888:49888 + 1200])
    print()
    print(f"=== 영업이익 @19435 ===")
    print(t2[19300:19435 + 700])
