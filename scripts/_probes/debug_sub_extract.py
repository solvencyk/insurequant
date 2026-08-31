# -*- coding: utf-8 -*-
import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
xml = ROOT / "data" / "dart" / "FY2026_Q2" / "raw" / "KR0011_DB손해보험" / "20260814003682.xml"
text = xml.read_text(encoding="utf-8", errors="replace")

for m in re.finditer(r"<TH[^>]*colspan=['\"]3['\"][^>]*>\s*후순위사채\s*</TH>", text):
    group_start = m.start()
    print("group_start =", group_start)
    header_block_end = text.find("</THEAD>", group_start)
    print("header_block_end =", header_block_end)
    header_block = text[group_start:header_block_end]
    print("---header_block---")
    print(repr(header_block[:600]))
    name_ths = re.findall(r"<TH[^>]*>(.*?)</TH>", header_block, re.DOTALL)
    print("name_ths raw:", name_ths)
    body_start = text.find("<TBODY>", header_block_end)
    body_end = text.find("</TBODY>", body_start)
    body = text[body_start:body_end]
    print("---body (first 500)---")
    print(repr(body[:500]))
    label = "사채, 명목금액"
    print("label in body:", label in body)
    idx = body.find(label)
    print("idx of label in body:", idx)
    if idx != -1:
        print(repr(body[idx-40:idx+300]))
    break
