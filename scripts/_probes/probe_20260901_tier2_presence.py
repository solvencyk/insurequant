# -*- coding: utf-8 -*-
"""KR0097 / KR1010 전분기 item47-54 존재 census."""
import json
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
recs = json.loads((ROOT/"kics_disclosure.json").read_text(encoding="utf-8"))
if isinstance(recs, dict): recs = recs.get("records") or recs.get("data") or []
by = {}
for r in recs:
    c,q = r.get("원보험사코드"), r.get("공시분기")
    try: it = int(r.get("항목번호"))
    except: continue
    by.setdefault((c,q),{})[it] = r
for code in ("KR0097","KR1010"):
    print(f"\n{'='*80}\n{code}")
    for (c,q),m in sorted(by.items()):
        if c != code: continue
        cells = []
        for i in range(47,55):
            r = m.get(i)
            if r is None: cells.append(f"{i}:—")
            else: cells.append(f"{i}:{r.get('값')}/{r.get('값_적용후')}")
        i3 = (m.get(3) or {}).get("값"); i13 = (m.get(13) or {}).get("값"); i1=(m.get(1) or {}).get("값")
        print(f"  {q:8s} i1={i1} i3={i3} i13={i13}")
        print(f"           {' '.join(cells)}")
