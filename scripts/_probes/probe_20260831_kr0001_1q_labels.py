# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

rows = json.loads(Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json").read_text(encoding="utf-8"))
recs = [r for r in rows if r["원보험사코드"]=="KR0001" and r["공시분기"]=="2026.1Q" and str(r["항목번호"]).isdigit() and int(r["항목번호"]) in (4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26)]
for r in sorted(recs, key=lambda r: int(r["항목번호"])):
    print(f"item{r['항목번호']:>2}: name={r['항목명']!r}  val={r['값']!r}  val_post={r.get('값_적용후')!r}")
print()
meta = next(r for r in rows if r["원보험사코드"]=="KR0001")
print("meta:", meta["원보험사코드"], meta["원수사명"], meta["티커"], meta["생손보여부"])
