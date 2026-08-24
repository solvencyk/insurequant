# -*- coding: utf-8 -*-
"""Text-density + keyword scan for the 3-company/6-quarter TFI backlog."""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

ROOT = Path(__file__).resolve().parents[2]

TARGETS = [
    ("KR1098", "2024.2Q", ROOT / "data/disclosure/FY2024_Q2/raw/KR1098_카카오페이손해보험_amended2.pdf"),
    ("KR1098", "2024.3Q", ROOT / "data/disclosure/FY2024_Q3/raw/KR1098_카카오페이손해보험.pdf"),
    ("KR1098", "2024.4Q", ROOT / "data/disclosure/FY2024_Q4/raw/KR1098_카카오페이손해보험.pdf"),
    ("KR0097", "2024.2Q", ROOT / "data/disclosure/FY2024_Q2/raw/KR0097_하나생명보험_amended.pdf"),
    ("KR0097", "2024.4Q", ROOT / "data/disclosure/FY2024_Q4/raw/KR0097_하나생명보험.pdf"),
    ("KR0071", "2024.4Q", ROOT / "data/disclosure/FY2024_Q4/raw/KR0071_흥국생명보험.pdf"),
]

for code, q, pdf in TARGETS:
    print(f"\n=== {code} {q}  {pdf.name} ===")
    if not pdf.exists():
        print("  FILE MISSING")
        continue
    doc = fitz.open(str(pdf))
    n = doc.page_count
    page_texts = [doc[i].get_text() for i in range(n)]
    total_chars = sum(len(t) for t in page_texts)
    density = total_chars / n if n else 0
    print(f"  pages={n}  total_chars={total_chars}  density={density:.1f}자/p")

    kw_pages = [i for i, t in enumerate(page_texts)
                if "공통적용" in t and "보완자본" in t and "한도" in t]
    print(f"  '공통적용'+'보완자본'+'한도' 동시등장 페이지(0-idx) = {kw_pages} (1-idx: {[p+1 for p in kw_pages]})")

    # also try weaker signals independently
    p_common = [i+1 for i, t in enumerate(page_texts) if "공통적용" in t]
    p_bowan = [i+1 for i, t in enumerate(page_texts) if "보완자본" in t]
    p_hando = [i+1 for i, t in enumerate(page_texts) if "한도" in t]
    p_gijun = [i+1 for i, t in enumerate(page_texts) if "지급여력기준금액" in t]
    p_gyeongwa = [i+1 for i, t in enumerate(page_texts) if "경과조치 적용에 관한" in t]
    print(f"  '공통적용' alone pages(1-idx)={p_common[:20]}")
    print(f"  '보완자본' alone pages(1-idx)={p_bowan[:20]}")
    print(f"  '지급여력기준금액' pages(1-idx)={p_gijun[:20]}")
    print(f"  '경과조치 적용에 관한' pages(1-idx)={p_gyeongwa[:20]}")

    # per-page char density around low-text pages (to find scanned image ranges)
    zero_pages = [i+1 for i, t in enumerate(page_texts) if len(t.strip()) < 20]
    print(f"  거의빈페이지(<20자) 개수={len(zero_pages)}/{n}  (예시 1-idx 앞10개: {zero_pages[:10]})")
    doc.close()
