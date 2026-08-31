import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

ROOT = Path(__file__).resolve().parents[2]


def find_pdf(period, code):
    for sub in ("pdf", "raw"):
        d = ROOT / "data" / "disclosure" / period / sub
        if not d.exists():
            continue
        for p in d.glob(f"{code}_*.pdf"):
            return p
    return None


samples = [
    ("FY2023_Q1", "KR0001"),
    ("FY2024_Q3", "KR0008"),
    ("FY2025_Q1", "KR0069"),
    ("FY2023_Q4", "KR0094"),
]

for period, code in samples:
    p = find_pdf(period, code)
    print(f"\n=== {period} {code} -> {p} ===")
    if not p:
        print("NOT FOUND")
        continue
    doc = fitz.open(str(p))
    hit = None
    for pno in range(min(8, len(doc))):
        t = doc[pno].get_text().replace(" ", "")
        if "주요경영지표" in t and "당기순이익" in t and "지급여력비율" in t:
            hit = pno
            break
    print(f"pages={len(doc)} hit_page={hit + 1 if hit is not None else None}")
    if hit is not None:
        print(doc[hit].get_text()[:900])
    doc.close()
