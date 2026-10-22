# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/KR0087_xml.py")
s = p.read_text(encoding="utf-8")
old = '''            j, txt, pline = i + 1, [], None
            while j < e and not lines[j].startswith("</TE") and not lines[j].startswith("</TH"):'''
new = '''            j, txt, pline = i + 1, [], None
            inline = re.search(r">([^<]*)</T[EH]>\s*$", l)
            if inline:                      # single-line cell: <TE ...>text</TE>
                txt.append(inline.group(1).replace("\u3000", " ").strip())
                pline = i + 1
                j = i
            while not inline and j < e and not lines[j].startswith("</TE") and not lines[j].startswith("</TH"):'''
assert s.count(old) == 1
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
