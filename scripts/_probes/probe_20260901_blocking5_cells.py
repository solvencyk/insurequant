# -*- coding: utf-8 -*-
"""blocking 5건의 마스터 셀 덤프 + 룰 detail 전문."""
import json, sys
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
recs = json.loads((ROOT/"kics_disclosure.json").read_text(encoding="utf-8"))
if isinstance(recs, dict): recs = recs.get("records") or recs.get("data") or []
rep = json.loads((ROOT/"artifacts/kics_validation/report_latest.json").read_text(encoding="utf-8"))

TARGETS = [("KR0080","2024.3Q"),("KR0097","2024.4Q"),("KR1010","2023.2Q"),
           ("KR1010","2023.3Q"),("KR0069","2024.4Q")]
by = {}
for r in recs:
    k = (r.get("원보험사코드"), r.get("공시분기"))
    if k in TARGETS:
        by.setdefault(k, []).append(r)

for k in TARGETS:
    rows = by.get(k, [])
    print(f"\n{'='*78}\n{k}  rows={len(rows)}")
    for f in rep["findings"]:
        if f.get("status")=="RED" and (f.get("원보험사코드"),f.get("공시분기"))==k:
            print(f"  [RED] {f.get('rule')}: expected={f.get('expected')} actual={f.get('actual')} diff={f.get('diff')}")
            print(f"        detail={f.get('detail')}")
    def num(x):
        try: return float(str(x).replace(",",""))
        except: return None
    for r in sorted(rows, key=lambda x: (int(x.get("항목번호") or 0))):
        it = r.get("항목번호"); nm = r.get("항목명")
        v, vp = r.get("값"), r.get("값_적용후")
        if it is None: continue
        try: iti = int(it)
        except: continue
        if iti in (1,2,3,4,12,13,14,20,21,29,30,31,32,33,34,35,47,48,49,50,51,52,53,54):
            print(f"    item{iti:<3} {str(nm)[:34]:36s} 값={v}  적용후={vp}")
