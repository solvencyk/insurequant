# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("KR0104_verify4q.py")
s = p.read_text(encoding="utf-8")
s = s.replace('x = sorted(d[0].glob("*.xml"))', 'x = [f for f in sorted(d[0].glob("*.xml")) if "_" not in f.stem]')
p.write_text(s, encoding="utf-8", newline="\n")
