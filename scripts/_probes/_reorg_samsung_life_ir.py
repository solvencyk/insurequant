#!/usr/bin/env python3
"""Reorganize 삼성생명 IR files into disclosure-style 공시분기>회사 layout:
data/ir/FY{YYYY}_Q{N}/KR0069_삼성생명/<file>. Maps each factsheet/PDF filename
to its publication quarter."""
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SRC = Path("data/ir/decks/samsung_life")
KR = "KR0069_삼성생명"


def fyq(fname: str) -> str | None:
    s = fname.replace(" ", "")
    m = re.search(r"1HFY(\d{2})", s)            # 상반기 → Q2 (check before annual)
    if m:
        return f"FY20{m.group(1)}_Q2"
    m = re.search(r"(\d)QFY(\d{2})", s)          # 1QFY26 / 3QFY25 / 4QFY24
    if m:
        return f"FY20{m.group(2)}_Q{m.group(1)}"
    m = re.search(r"(?<![\dQH])FY(\d{2})Factsheet", s)   # 연간 (no quarter prefix) → Q4
    if m:
        return f"FY20{m.group(1)}_Q4"
    m = re.search(r"FY(\d{2})_(\d)Q", fname) or re.search(r"20(\d{2})_(\d)Q", fname)
    if m:
        return f"FY20{m.group(1)}_Q{m.group(2)}"
    return None


def main():
    moved = []
    for f in sorted(SRC.glob("*")):
        if f.name == "series.json" or f.is_dir():
            continue
        q = fyq(f.name)
        if not q:
            print("  ?? no quarter:", f.name)
            continue
        dest = Path("data/ir") / q / KR / f.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        moved.append((q, f.name))
    for q, n in sorted(moved):
        print(f"  {q}/{KR}/{n}")
    print(f"reorganized {len(moved)} files")
    # keep the aggregated series under data/ir/series/
    ser = SRC / "series.json"
    if ser.exists():
        out = Path("data/ir/series")
        out.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ser, out / f"{KR}.json")
        print(f"  series → data/ir/series/{KR}.json")


if __name__ == "__main__":
    main()
