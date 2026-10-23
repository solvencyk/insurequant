# -*- coding: utf-8 -*-
"""read-only: <TITLE> list (line, text) of KDB filings (old FY2023 and new FY2024)."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = "data/dart"
FILES = {
    "O1": f"{D}/FY2023_Q1/raw/KR0072_케이디비생명보험/xml/20230515002450.xml",
    "O2": f"{D}/FY2023_Q2/raw/KR0072_케이디비생명보험/xml/20230814003052.xml",
    "O3": f"{D}/FY2023_Q3/raw/KR0072_케이디비생명보험/xml/",
    "O4": f"{D}/FY2023_Q4/raw/KR0072_케이디비생명보험_20240401002710/xml/",
    "N1": f"{D}/FY2024_Q1/raw/KR0072_케이디비생명보험/20240516000597.xml",
    "N2": f"{D}/FY2024_Q2/raw/KR0072_케이디비생명보험/20240814000801.xml",
    "N3": f"{D}/FY2024_Q3/raw/KR0072_케이디비생명보험/20241114000809.xml",
    "N4": f"{D}/FY2024_Q4/raw/KR0072_케이디비생명보험_20250331002302/20250331002302.xml",
}
for k, rel in FILES.items():
    p = ROOT / rel
    if p.is_dir():
        print(k, "DIR", [x.name for x in p.iterdir()])
        continue
    if not p.exists():
        print(k, "MISSING", rel)
        continue
    L = p.read_text(encoding="utf-8", errors="replace").split("\n")
    print("=====", k, rel, len(L), "lines")
    for i, s in enumerate(L):
        if s.startswith("<TITLE"):
            t = re.sub(r"<[^>]+>", "", s).strip()
            if re.match(r"^(\d+(-\d+)?\.|[IVX]+\.)", t) or "주석" in t or "재무" in t:
                print(f"  L{i+1}: {t[:90]}")
