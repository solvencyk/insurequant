# -*- coding: utf-8 -*-
"""DB손해보험(KR0011) 2023.2Q raw: '보험영업' 뒤에 오는 글자들 + 요약 손익계산서 후보
캡션 스캔 (read-only)."""
import re
import sys
from collections import Counter
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
    suf = Counter()
    for m in re.finditer(r"보험영업(.{0,4})", t2):
        suf[m.group(1)[:2]] += 1
    print(f"[{x.name}] 보험영업+2글자 분포:", suf.most_common(10))
    # 요약 재무정보/포괄손익계산서 캡션들
    for kw in ("요약재무정보", "요약포괄손익계산서", "포괄손익계산서", "영업이익", "당기순이익"):
        idxs = [m.start() for m in re.finditer(re.escape(kw), t2)]
        print(f"  {kw}: {len(idxs)}회, 처음 3개 offset={idxs[:3]}")
