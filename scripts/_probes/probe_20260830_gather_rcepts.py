import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

targets = [
    "data/dart/FY2023_Q1/raw/KR0079_미래에셋생명",
    "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명",
    "data/dart/FY2025_Q3/raw/KR0079_미래에셋생명",
    "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664",
    "data/dart/FY2026_Q1/raw/KR0079_미래에셋생명",
    "data/dart/FY2023_Q1/raw/KR0003_롯데손해보험",
    "data/dart/FY2023_Q2/raw/KR0003_롯데손해보험",
    "data/dart/FY2024_Q2/raw/KR0003_롯데손해보험",
    "data/dart/FY2023_Q1/raw/KR0072_케이디비생명보험",
    "data/dart/FY2023_Q2/raw/KR0072_케이디비생명보험",
]
for t in targets:
    p = ROOT / t / "meta.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        print(f"{t}\n  rcept={d.get('rcept_no')} kind={d.get('report_kind')} period={d.get('period')}\n")
    else:
        print(f"{t}\n  meta.json NOT FOUND\n")
