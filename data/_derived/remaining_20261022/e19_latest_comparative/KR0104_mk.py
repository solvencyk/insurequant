# -*- coding: utf-8 -*-
from pathlib import Path
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
new = '''FILES = {
 "FY2023_Q1": "data/dart/FY2023_Q1/raw/KR0104_농협생명보험/20230515002904.xml",
 "FY2023_Q2": "data/dart/FY2023_Q2/raw/KR0104_농협생명보험/20230814001979.xml",
 "FY2023_Q3": "data/dart/FY2023_Q3/raw/KR0104_농협생명보험/20231114001637.xml",
 "FY2023_Q4": "data/dart/FY2023_Q4/raw/KR0104_농협생명보험_20240401002122/20240401002122.xml",
 "FY2024_Q1": "data/dart/FY2024_Q1/raw/KR0104_농협생명보험/20240514001371.xml",
 "FY2024_Q2": "data/dart/FY2024_Q2/raw/KR0104_농협생명보험/20240814002115.xml",
 "FY2024_Q3": "data/dart/FY2024_Q3/raw/KR0104_농협생명보험/20241114000851.xml",
 "FY2024_Q4": "data/dart/FY2024_Q4/raw/KR0104_농협생명보험_20250331003065/20250331003065.xml",
}
'''
s = (H / "KR0082_xml.py").read_text(encoding="utf-8")
a = s.index("FILES = {")
b = s.index("}\n", a) + 2
s = s[:a] + new + s[b:]
s = s.replace("KR0082", "KR0104")
(H / "KR0104_xml.py").write_text(s, encoding="utf-8", newline="\n")
for n in ("dump_stmt", "dump_master", "dump_census", "dump_csm", "view_d5", "peek_gold", "titles"):
    p = H / f"KR0082_{n}.py"
    t = p.read_text(encoding="utf-8").replace("KR0082", "KR0104")
    if n == "titles":
        a = t.index("FILES = {"); b = t.index("}\n", a) + 2
        t = t[:a] + new + t[b:]
    (H / f"KR0104_{n}.py").write_text(t, encoding="utf-8", newline="\n")
