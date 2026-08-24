# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / "data/disclosure/FY2023_Q1/raw"
import glob
p = glob.glob(str(pdf / "KR0075_*"))
print(p)
doc = fitz.open(p[0])
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "공통적용" in t and "보완자본" in t and "한도" in t:
        print(f"=== page idx {i} ===")
        print(t)
    if "경과조치를 적용" in t or "경과조치를 신청" in t:
        print(f"--- page idx {i} mentions 경과조치 적용/신청 ---")
        for line in t.splitlines():
            if "경과조치" in line:
                print("  ", line)
doc.close()
