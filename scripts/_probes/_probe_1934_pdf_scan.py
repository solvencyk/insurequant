import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

KEYS = ["금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험액", "순자산가치"]

TARGETS = {
    "KR0004": "data/disclosure/FY2026_Q2/pdf/KR0004_MG_예별손해보험.pdf",
    "KR0011": "data/disclosure/FY2026_Q2/pdf/KR0011_DB손해보험.pdf",
    "KR0029": "data/disclosure/FY2026_Q2/pdf/KR0029_AIG손해보험.pdf",
    "KR0051": "data/disclosure/FY2026_Q2/pdf/KR0051_신한이지손해보험.pdf",
    "KR0068": "data/disclosure/FY2026_Q2/pdf/KR0068_한화생명.pdf",
    "KR0080": "data/disclosure/FY2026_Q2/pdf/KR0080_에이아이에이생명보험.pdf",
    "KR0087": "data/disclosure/FY2026_Q2/pdf/KR0087_동양생명.pdf",
    "KR0094": "data/disclosure/FY2026_Q2/pdf/KR0094_신한라이프생명보험.pdf",
    "KR0099": "data/disclosure/FY2026_Q2/pdf/KR0099_케이비라이프생명보험.pdf",
    "KR0100": "data/disclosure/FY2026_Q2/pdf/KR0100_처브라이프생명보험.pdf",
    "KR0104": "data/disclosure/FY2026_Q2/pdf/KR0104_농협생명보험.pdf",
    "KR1098": "data/disclosure/FY2026_Q2/pdf/KR1098_카카오페이손해보험.pdf",
    "KR0072": "data/disclosure/FY2026_Q2/pdf/KR0072_케이디비생명보험.pdf",
    "KR1010": "data/disclosure/FY2026_Q2/pdf/KR1010_교보라이프플래닛생명보험.pdf",
}

for code, path in TARGETS.items():
    doc = fitz.open(path)
    print(f"=== {code} ({doc.page_count} pages) ===")
    for i in range(doc.page_count):
        t = doc[i].get_text()
        hits = [k for k in KEYS if k in t]
        if hits:
            print(f"  p{i+1} (idx{i}): chars={len(t)} hits={hits}")
    doc.close()
    print()
