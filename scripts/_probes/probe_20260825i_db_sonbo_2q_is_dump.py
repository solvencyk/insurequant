# -*- coding: utf-8 -*-
"""DB손해보험(KR0011) 2023.2Q raw 요약(연결)포괄손익계산서 전체 덤프 (read-only)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

dirs = sorted((ROOT / "data/dart/FY2023_Q2/raw").glob("KR0011_*"))
print("dirs:", [d.name for d in dirs])
for d in dirs:
    for x in sorted(d.glob("*.xml")):
        raw = x.read_bytes()
        try:
            t = raw.decode("utf-8")
        except UnicodeDecodeError:
            t = raw.decode("cp949", errors="replace")
        t2 = re.sub(r"<[^>]+>", " ", t)
        t2 = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", t2)
        t2 = re.sub(r"\s+", " ", t2)
        for m in re.finditer(r"보험손익", t2):
            ctx = t2[max(0, m.start() - 60): m.start() + 400]
            print(f"[{x.name}] @{m.start()}: ...{ctx}...")
            print()
