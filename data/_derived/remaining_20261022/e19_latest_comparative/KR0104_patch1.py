# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("KR0104_verify.py")
s = p.read_text(encoding="utf-8")
s = s.replace('    h2 = get(F2, LABEL[it], 4)\n', '    h2 = get(F2, LABEL[it], 4) or get(F2, "반기순이익" if it == 24 else LABEL[it], 4)\n')
p.write_text(s, encoding="utf-8", newline="\n")
