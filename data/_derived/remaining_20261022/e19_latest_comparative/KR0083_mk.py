# -*- coding: utf-8 -*-
from pathlib import Path
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
s = (H / "KR0070_xml.py").read_text(encoding="utf-8")
a = s.index("FILES = {")
b = s.index("}\n", a) + 2
new = '''FILES = {
 "FY2023_Q4": "data/dart/FY2023_Q4/raw/KR0083_푸본현대생명보험_20240329002122/20240329002122.xml",
 "FY2024_Q1": "data/dart/FY2024_Q1/raw/KR0083_푸본현대생명보험/20240516000426.xml",
 "FY2024_Q2": "data/dart/FY2024_Q2/raw/KR0083_푸본현대생명보험/20240814002545.xml",
 "FY2024_Q3": "data/dart/FY2024_Q3/raw/KR0083_푸본현대생명보험/20241114000568.xml",
 "FY2024_Q4": "data/dart/FY2024_Q4/raw/KR0083_푸본현대생명보험_20250328000873/20250328000873.xml",
 "FY2025_Q1": "data/dart/FY2025_Q1/raw/KR0083_푸본현대생명보험/20250515002207.xml",
 "FY2025_Q2": "data/dart/FY2025_Q2/raw/KR0083_푸본현대생명보험/20250814001834.xml",
 "FY2025_Q3": "data/dart/FY2025_Q3/raw/KR0083_푸본현대생명보험/20251114001046.xml",
 "FY2025_Q4": "data/dart/FY2025_Q4/raw/KR0083_푸본현대생명보험_20260331002089/20260331002089.xml",
}
'''
s = s[:a] + new + s[b:]
s = s.replace("KR0070", "KR0083")
(H / "KR0083_xml.py").write_text(s, encoding="utf-8", newline="\n")
d = (H / "KR0070_dump_stmt.py").read_text(encoding="utf-8").replace("KR0070", "KR0083")
(H / "KR0083_dump_stmt.py").write_text(d, encoding="utf-8", newline="\n")
d = (H / "KR0070_dump_master.py").read_text(encoding="utf-8").replace("KR0070", "KR0083")
(H / "KR0083_dump_master.py").write_text(d, encoding="utf-8", newline="\n")
for n in ("dump_census","dump_csm","view_d5"):
    p = H / f"KR0070_{n}.py"
    if p.exists():
        (H / f"KR0083_{n}.py").write_text(p.read_text(encoding="utf-8").replace("KR0070", "KR0083"), encoding="utf-8", newline="\n")
