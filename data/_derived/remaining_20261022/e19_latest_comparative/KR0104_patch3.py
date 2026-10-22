# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("KR0104_verify.py")
s = p.read_text(encoding="utf-8")
s = s.replace('h = get(O3, lab, 4)\n    orig[it]', 'h = get(O3, lab, 2)\n    orig[it]')
s = s.replace('fe0 = get(O3, "보험금융비용", 4)\nre0 = get(O3, "재보험금융비용", 4)', 'fe0 = get(O3, "보험금융비용", 2)\nre0 = get(O3, "재보험금융비용", 2)')
s = s.replace('for i in range(ob, ob + 140) for t in re.findall(r"<P>(.*)</P>", ols[i]) if t.strip()][:14]', 'for i in range(ob, ob + 400) for t in re.findall(r"<P[^>]*>(.*)</P>", ols[i]) if "단위" in t or "제 12" in t or "제 11" in t or t in ("3개월", "누적")]')
p.write_text(s, encoding="utf-8", newline="\n")
