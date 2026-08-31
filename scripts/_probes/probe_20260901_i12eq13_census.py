# -*- coding: utf-8 -*-
"""item12 == item13 (다리 표 두 행 병합) 지문 전수 census + KR0080 전분기."""
import json, sys, collections
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
recs = json.loads((ROOT/"kics_disclosure.json").read_text(encoding="utf-8"))
if isinstance(recs, dict): recs = recs.get("records") or recs.get("data") or []
def num(x):
    try: return float(str(x).replace(",",""))
    except: return None
by = {}
for r in recs:
    c,q = r.get("원보험사코드"), r.get("공시분기")
    try: it = int(r.get("항목번호"))
    except: continue
    by.setdefault((c,q),{})[it] = (num(r.get("값")), num(r.get("값_적용후")), r.get("원수사명"))

print("== KR0080 전분기 (item2/3/4/12/13) ==")
for (c,q),m in sorted(by.items()):
    if c!="KR0080": continue
    g=lambda i: (m.get(i) or (None,None,None))[0]
    i2,i3,i4,i12,i13 = g(2),g(3),g(4),g(12),g(13)
    br = None if None in (i4,i12,i13) else i4-i12-i13
    ok = "" if (br is None or i2 is None) else ("  <== 다리잔차 %+.1f"%(i2-br))
    dup = "  [i12==i13]" if (i12 is not None and i13 is not None and abs(i12-i13)<1e-9) else ""
    print(f"  {q:8s} i2={i2} i3={i3} i4={i4} i12={i12} i13={i13} 다리={br}{ok}{dup}")

print("\n== 전수: item12 == item13 이면서 item13 == item3 아닌 버킷 (병합 의심) ==")
n=0
for (c,q),m in sorted(by.items()):
    g=lambda i: (m.get(i) or (None,None,None))[0]
    i2,i3,i4,i12,i13 = g(2),g(3),g(4),g(12),g(13)
    if i12 is None or i13 is None: continue
    if abs(i12-i13) > 1e-9: continue
    nm = (m.get(12) or (None,None,None))[2]
    br = None if None in (i4,i12,i13) else i4-i12-i13
    res = None if (br is None or i2 is None) else i2-br
    # 대체가설: i13 이 사실 i3 여야 하는가
    br2 = None if None in (i4,i12,i3) else i4-i12-i3
    res2 = None if (br2 is None or i2 is None) else i2-br2
    flag = ""
    if res is not None and res2 is not None and abs(res2) < abs(res) and abs(res2) <= 2:
        flag = "  <<< i13:=i3 로 바꾸면 닫힌다"
        n+=1
    print(f"  {c} {str(nm)[:12]:14s} {q:8s} i3={i3} i12=i13={i12} 잔차(현행)={res} 잔차(i13:=i3)={res2}{flag}")
print("  병합의심 합계 =", n)
