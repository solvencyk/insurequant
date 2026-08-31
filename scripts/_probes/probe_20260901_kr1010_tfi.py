# -*- coding: utf-8 -*-
"""KR1010 2023.2Q/2023.3Q raw — TFI(공통적용 경과조치) 표 실재 여부 재확인."""
from pathlib import Path
import fitz
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
for q, fy in (("2023.2Q","FY2023_Q2"), ("2023.3Q","FY2023_Q3")):
    pdf = ROOT / f"data/disclosure/{fy}/raw/KR1010_교보라이프플래닛생명보험.pdf"
    print(f"\n{'='*76}\n{q}  {pdf.name}  exists={pdf.exists()}")
    if not pdf.exists(): continue
    doc = fitz.open(pdf)
    tot = 0
    for p in range(doc.page_count):
        tot += len(doc[p].get_text())
    print(f"  pages={doc.page_count} chars={tot} (밀도 {tot/max(1,doc.page_count):.0f}/p)")
    for p in range(doc.page_count):
        t = doc[p].get_text()
        if "공통적용" in t or ("보완자본" in t and "한도" in t):
            print(f"  -- page {p+1}: 공통적용={'공통적용' in t} 보완자본한도={'보완자본' in t and '한도' in t}")
            for ln in t.splitlines():
                s = ln.strip()
                if any(k in s for k in ("공통적용","보완자본","한도","해약환급금","지급여력금액","기본자본","경과조치")):
                    print("       ", s[:150])
