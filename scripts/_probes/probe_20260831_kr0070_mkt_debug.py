# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\scripts")
import fill_market_subitems_to_disclosure as fm
from pathlib import Path

MD = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\md_inbox\FY2026_Q2\KR0070_에이비엘생명보험.md")
text = MD.read_text(encoding="utf-8")
subs = fm.extract_mkt_subs(text)
print("extract_mkt_subs (with fix):", subs)
for item_no, (val, unit) in sorted(subs.items()):
    eok = fm._to_eok(val, unit)
    print(f"  item{item_no}: raw={val!r} unit={unit} -> {eok} 억원")
v5 = [float(fm._to_eok(*subs.get(n, ("0","백만원")))) for n in (36,37,38,39,40)]
print("v5:", v5, "est:", fm.mkt_est(v5))
