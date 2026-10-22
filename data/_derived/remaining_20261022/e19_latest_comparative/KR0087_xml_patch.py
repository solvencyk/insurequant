# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/KR0087_xml.py")
s = p.read_text(encoding="utf-8")
old = '''            if "ACONTEXT" in attrs:
                cur["cells"].append({"acode": attrs.get("ACODE"), "ctx": attrs["ACONTEXT"], "text": text, "val": num(text), "line": pline, "dec": attrs.get("ADECIMAL")})
            elif cur["label"] is None:
                cur["label"] = (text, pline)'''
new = '''            if cur["label"] is None:
                cur["label"] = (text, pline)
            else:
                cur["cells"].append({"acode": attrs.get("ACODE"), "ctx": attrs.get("ACONTEXT", ""), "text": text, "val": num(text), "line": pline, "dec": attrs.get("ADECIMAL")})'''
assert s.count(old) == 1
p.write_text(s.replace(old, new), encoding="utf-8", newline="\n")
