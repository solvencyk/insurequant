# -*- coding: utf-8 -*-
from pathlib import Path
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
s = (H / "KR0083_xml.py").read_text(encoding="utf-8")
a = s.index("FILES = {")
b = s.index("}\n", a) + 2
new = '''FILES = {
 "FY2023_Q1": "data/dart/FY2023_Q1/raw/KR0082_DB생명보험/20230515002932.xml",
 "FY2023_Q2": "data/dart/FY2023_Q2/raw/KR0082_DB생명보험/20230814002739.xml",
 "FY2023_Q3": "data/dart/FY2023_Q3/raw/KR0082_DB생명보험/20231114002805.xml",
 "FY2023_Q4": "data/dart/FY2023_Q4/raw/KR0082_DB생명보험_20240329001728/20240329001728.xml",
 "FY2024_Q1": "data/dart/FY2024_Q1/raw/KR0082_DB생명보험/20240514000901.xml",
 "FY2024_Q2": "data/dart/FY2024_Q2/raw/KR0082_DB생명보험/20240814000663.xml",
 "FY2024_Q3": "data/dart/FY2024_Q3/raw/KR0082_DB생명보험/20241114001831.xml",
 "FY2024_Q4": "data/dart/FY2024_Q4/raw/KR0082_DB생명보험_20250328002241/20250328002241.xml",
}
'''
s = s[:a] + new + s[b:]
s = s.replace("KR0083", "KR0082")
(H / "KR0082_xml.py").write_text(s, encoding="utf-8", newline="\n")
for n in ("dump_stmt", "dump_master", "dump_census", "dump_csm", "view_d5", "peek_gold", "titles"):
    p = H / f"KR0083_{n}.py"
    t = p.read_text(encoding="utf-8").replace("KR0083", "KR0082")
    if n == "titles":
        a = t.index("FILES = {"); b = t.index("}\n", a) + 2
        t = t[:a] + new + t[b:]
    (H / f"KR0082_{n}.py").write_text(t, encoding="utf-8", newline="\n")
