#!/usr/bin/env python3
"""② 후속: 삼성생명 잔차 5분기에서 PL 이 왜 연결을 무는지 — ATOC 경계 + line_no 실측."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from scripts.pl_breakdown.common import _ofs_line_boundary

QS = ["FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2023_Q4",
      "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4",
      "FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2025_Q4",
      "FY2026_Q1", "FY2026_Q2"]
OPEN = {"2024.1Q", "2024.2Q", "2024.3Q", "2025.2Q", "2026.2Q"}

print(f"{'분기':9s} {'잔차':4s} {'파일':34s} {'줄수':>8s} {'ATOC경계':>9s} {'>65535?':>8s}")
for q in QS:
    dirs = sorted((ROOT / "data" / "dart" / q / "raw").glob("KR0069_*"))
    if not dirs:
        print(f"{q}: raw 없음"); continue
    qq = q.replace("FY", "").replace("_Q", ".") + "Q"
    for x in sorted(dirs[0].glob("*.xml")):
        n = sum(1 for _ in open(x, encoding="utf-8", errors="replace"))
        b = _ofs_line_boundary(x)
        flag = "YES" if (b or 0) > 65535 else ("-" if b else "n/a")
        print(f"{qq:9s} {'OPEN' if qq in OPEN else '  · ':4s} {x.name:34s} {n:>8,} {str(b):>9s} {flag:>8s}")
