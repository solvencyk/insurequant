# -*- coding: utf-8 -*-
"""DB손해보험(KR0011) 2023.2Q raw '보험영업손익' 주변 텍스트 덤프 (read-only)."""
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
    for m in re.finditer(r"보험영업손익", t2):
        ctx = t2[max(0, m.start() - 100): m.start() + 500]
        print(f"[{x.name}] @{m.start()}: ...{ctx}...")
        print()
