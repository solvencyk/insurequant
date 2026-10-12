"""Read-only evidence for the wrong-year-column fix of KR0002 (한화손해보험) item 16 기타사업비용, 2023.1Q and 2023.2Q.

The master holds 39,900 / 84,500 (= the 24.1Q / 24.2Q figures 399 / 845 억원 of the FY2024 filings' '해당 분기' column).  The 전년 동기 (23.xQ) column of the same FY2024 PDFs and the
OWN FY2023 filings print 257 / 529 억원.  This script re-reads the four PDFs (PyMuPDF text, independent of the production reader) and writes evidence_kr0002_item16.json.
Also the FY2023_Q3 own filing (803억 = master 80,303.18 백만원 FS-API) for the series-consistency check."""
import json
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FILES = {
    "own_2023_Q1": "data/disclosure/FY2023_Q1/raw/KR0002_한화손해보험.pdf",
    "later_2024_Q1": "data/disclosure/FY2024_Q1/raw/KR0002_한화손해보험.pdf",
    "own_2023_Q2": "data/disclosure/FY2023_Q2/raw/KR0002_한화손해보험.pdf",
    "later_2024_Q2": "data/disclosure/FY2024_Q2/raw/KR0002_한화손해보험.pdf",
    "own_2023_Q3": "data/disclosure/FY2023_Q3/raw/KR0002_한화손해보험.pdf",
}
res = {}
for tag, rel in FILES.items():
    doc = fitz.open(str(ROOT / rel))
    for pno in range(0, 10):
        lines = [l.strip() for l in doc[pno].get_text().splitlines()]
        if not any("요약 포괄손익계산서" in l for l in lines):
            continue
        hdr = [l for l in lines[:30] if re.search(r"\(\d\d\.\dQ\)|\(2\d\.\dQ\)", l) or "해당 분기" in l or "당기" == l or "전년" in l]
        for i, l in enumerate(lines):
            if l == "기타사업비용":
                nums = lines[i + 1:i + 4]
                res[tag] = {"file": rel, "page": pno + 1, "header_lines": hdr, "row": ["기타사업비용"] + nums}
                break
        if tag in res:
            break
print(json.dumps(res, ensure_ascii=False, indent=1))
(HERE / "evidence_kr0002_item16.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
