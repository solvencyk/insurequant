import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
for p in sorted((ROOT / "data/dart/FY2023_Q2/raw").glob("KR0079_*")):
    print("dir:", p)
    for x in sorted(p.rglob("*")):
        print("  ", x.relative_to(p), "(dir)" if x.is_dir() else f"({x.stat().st_size}b)")
