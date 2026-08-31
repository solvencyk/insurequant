# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

rows = json.loads(Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json").read_text(encoding="utf-8"))
items_3646 = [r for r in rows if str(r["항목번호"]).isdigit() and 36 <= int(r["항목번호"]) <= 46]
has_post = sum(1 for r in items_3646 if r.get("값_적용후") not in (None, "", "None"))
print(f"items 36-46 total rows={len(items_3646)}  with 값_적용후={has_post}")
# and for ABL/DB specifically at 2026.1Q (a TAC-applying quarter) to see the pattern
for code in ["KR0070", "KR0082"]:
    recs = [r for r in rows if r["원보험사코드"]==code and r["공시분기"]=="2026.1Q" and str(r["항목번호"]).isdigit() and 36<=int(r["항목번호"])<=40]
    for r in recs:
        print(f"  {code} 2026.1Q item{r['항목번호']}: val={r['값']!r} post={r.get('값_적용후')!r}")
