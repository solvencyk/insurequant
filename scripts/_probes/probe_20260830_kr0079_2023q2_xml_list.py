import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
for p in sorted((ROOT / "data/dart/FY2023_Q2/raw").glob("KR0079_*")):
    print("dir:", p)
    for x in sorted((p / "xml").glob("*.xml")):
        t = x.read_text(encoding="utf-8", errors="replace")
        print(" ", x.name, len(t), "chars",
              "| 기초순장부금액:", t.count("기초순장부금액"),
              "| 신계약효과:", t.count("신계약효과"),
              "| 기말순장부금액:", t.count("기말순장부금액"))
