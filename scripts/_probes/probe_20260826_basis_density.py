#!/usr/bin/env python3
"""파일을 구간으로 잘라 '연결실체' vs '당사' 밀도를 재서 연결/별도 섹션 경계를 찾는다."""
import sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
p = Path(sys.argv[1])
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
STEP = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
marks = [int(x) for x in sys.argv[3:]]
print(f"{p.name}  lines={len(lines):,}")
print(f"{'구간':>18s} {'연결실체':>7s} {'당사':>5s} {'연결(단어)':>9s}")
for s in range(0, len(lines), STEP):
    chunk = "\n".join(lines[s:s + STEP])
    c = chunk.count("연결실체")
    d = len(re.findall(r"당사(는|의|가)", chunk))
    g = chunk.count("연결")
    flag = "".join(" <<%d" % m for m in marks if s < m <= s + STEP)
    print(f"{s+1:>8,}-{min(s+STEP,len(lines)):>8,} {c:>7} {d:>5} {g:>9}{flag}")
