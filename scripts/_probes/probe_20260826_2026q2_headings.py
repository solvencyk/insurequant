#!/usr/bin/env python3
"""TITLE 태그가 없는 HTML 템플릿(2026.2Q)에서 연결/별도 섹션 경계 후보 찾기."""
import sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
p = Path(sys.argv[1])
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()

# 짧은 문단 = 제목 후보
cands = []
for i, l in enumerate(lines, 1):
    if "재무제표" not in l:
        continue
    t = strip(l)
    if 2 <= len(t) <= 40:
        cands.append((i, t))
print(f"짧은 '재무제표' 문단 {len(cands)}건")
for i, t in cands[:40]:
    print(f"  L{i:>7,}  {t}")
print()
for target in [int(x) for x in sys.argv[2:]]:
    print(f"--- L{target:,} 직전 짧은 제목 후보 ---")
    prev = [c for c in cands if c[0] <= target][-4:]
    for i, t in prev:
        print(f"   L{i:>7,}  {t}")
