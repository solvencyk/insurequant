# -*- coding: utf-8 -*-
from pathlib import Path
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
s = (H / "KR0087_xml.py").read_text(encoding="utf-8")
a = s.index("FILES = {")
b = s.index("}\n", a) + 2
new = '''FILES = {
 "FY2023_Q4": "data/dart/FY2023_Q4/raw/KR0070_에이비엘생명보험_20240329001518/xml/20240329001518.xml",
 "FY2024_Q1": "data/dart/FY2024_Q1/raw/KR0070_에이비엘생명보험/20240516002045.xml",
 "FY2024_Q2": "data/dart/FY2024_Q2/raw/KR0070_에이비엘생명보험/20240814004092.xml",
 "FY2024_Q3": "data/dart/FY2024_Q3/raw/KR0070_에이비엘생명보험/20241114002738.xml",
 "FY2024_Q4": "data/dart/FY2024_Q4/raw/KR0070_에이비엘생명보험_20250331001358/20250331001358.xml",
 "FY2025_Q1": "data/dart/FY2025_Q1/raw/KR0070_에이비엘생명보험/20250515002435.xml",
 "FY2025_Q2": "data/dart/FY2025_Q2/raw/KR0070_에이비엘생명보험/20250814004404.xml",
 "FY2025_Q3": "data/dart/FY2025_Q3/raw/KR0070_에이비엘생명보험/20251114002593.xml",
 "FY2025_Q4": "data/dart/FY2025_Q4/raw/KR0070_에이비엘생명보험_20260331003080/20260331003080.xml",
}
'''
s = s[:a] + new + s[b:]
s = s.replace("KR0087", "KR0070")
(H / "KR0070_xml.py").write_text(s, encoding="utf-8", newline="\n")
d = (H / "KR0087_dump_stmt.py").read_text(encoding="utf-8").replace("KR0087", "KR0070")
(H / "KR0070_dump_stmt.py").write_text(d, encoding="utf-8", newline="\n")
