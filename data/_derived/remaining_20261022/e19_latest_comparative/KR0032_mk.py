# -*- coding: utf-8 -*-
from pathlib import Path
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
s = (H / "KR0087_xml.py").read_text(encoding="utf-8")
a = s.index("FILES = {")
b = s.index("}\n", a) + 2
new = '''FILES = {
 "FY2023_Q1": "data/dart/FY2023_Q1/raw/KR0032_NH농협손해보험/20230515002460.xml",
 "FY2023_Q2": "data/dart/FY2023_Q2/raw/KR0032_NH농협손해보험/20230814001056.xml",
 "FY2023_Q3": "data/dart/FY2023_Q3/raw/KR0032_NH농협손해보험/20231114000995.xml",
 "FY2023_Q4": "data/dart/FY2023_Q4/raw/KR0032_NH농협손해보험_20240329001662/20240329001662.xml",
 "FY2024_Q1": "data/dart/FY2024_Q1/raw/KR0032_NH농협손해보험/20240514001436.xml",
 "FY2024_Q2": "data/dart/FY2024_Q2/raw/KR0032_NH농협손해보험/20240814001448.xml",
 "FY2024_Q3": "data/dart/FY2024_Q3/raw/KR0032_NH농협손해보험/20241114001354.xml",
 "FY2024_Q4": "data/dart/FY2024_Q4/raw/KR0032_NH농협손해보험_20250331003247/20250331003247.xml",
 "FY2025_Q1": "data/dart/FY2025_Q1/raw/KR0032_NH농협손해보험/20250515001078.xml",
 "FY2025_Q2": "data/dart/FY2025_Q2/raw/KR0032_NH농협손해보험/20250814001701.xml",
 "FY2025_Q3": "data/dart/FY2025_Q3/raw/KR0032_NH농협손해보험/20251114001790.xml",
 "FY2025_Q4": "data/dart/FY2025_Q4/raw/KR0032_NH농협손해보험_20260331004099/20260331004099.xml",
}
'''
s = s[:a] + new + s[b:]
s = s.replace("KR0087", "KR0032")
(H / "KR0032_xml.py").write_text(s, encoding="utf-8", newline="\n")
d = (H / "KR0087_dump_stmt.py").read_text(encoding="utf-8").replace("KR0087", "KR0032")
d = d.replace("for fy in X.FILES:", "for fy in [k for k in X.FILES if k not in ('FY2023_Q1','FY2023_Q2')]:")
(H / "KR0032_dump_stmt.py").write_text(d, encoding="utf-8", newline="\n")
d = (H / "KR0087_dump_master.py").read_text(encoding="utf-8").replace("KR0087", "KR0032")
(H / "KR0032_dump_master.py").write_text(d, encoding="utf-8", newline="\n")
d = (H / "KR0087_dump_census.py").read_text(encoding="utf-8").replace("KR0087", "KR0032")
(H / "KR0032_dump_census.py").write_text(d, encoding="utf-8", newline="\n")
d = (H / "KR0087_dump_csm.py").read_text(encoding="utf-8").replace("KR0087", "KR0032")
(H / "KR0032_dump_csm.py").write_text(d, encoding="utf-8", newline="\n")
