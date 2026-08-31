# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0049"]
quarters = sorted(set(r.get("공시분기") for r in rows))

def fnum(x):
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

for q in quarters:
    qrows = {r["항목번호"]: r for r in rows if r.get("공시분기") == q and r.get("항목번호") is not None}
    def v(i):
        r = qrows.get(i)
        return fnum(r.get("값")) if r else None
    def vp(i):
        r = qrows.get(i)
        return fnum(r.get("값_적용후")) if r else None

    i1, i3, i14 = v(1), v(3), v(14)
    i47, i48, i49 = v(47), v(48), v(49)
    i1p, i3p, i14p = vp(1), vp(3), vp(14)
    i47p, i48p, i49p = vp(47), vp(48), vp(49)
    i54, i54p = v(54), vp(54)

    print(f"=== {q} ===")
    print(f"  전: item1={i1} item3={i3} item14={i14} item47={i47} item48={i48} item49={i49} item54={i54}")
    if None not in (i3, i47, i48, i49):
        excl = min(i47, i48) + i49
        incl = min(i47 - i49, i48) + i49
        print(f"      EXCL(min(47,48)+49)={excl:.2f} vs item3={i3:.2f} diff={excl-i3:.2f}")
        print(f"      INCL(min(47-49,48)+49)={incl:.2f} vs item3={i3:.2f} diff={incl-i3:.2f}")
    if i14 is not None:
        print(f"      item14*0.5={i14*0.5:.2f} vs item48={i48}")
    print(f"  후: item1={i1p} item3={i3p} item14={i14p} item47={i47p} item48={i48p} item49={i49p} item54={i54p}")
    if None not in (i3p, i47p, i48p, i49p):
        exclp = min(i47p, i48p) + i49p
        inclp = min(i47p - i49p, i48p) + i49p
        exclp54 = min(i47p, i48p) + i49p + (i54p or 0)
        print(f"      EXCL(min(47,48)+49)={exclp:.2f} vs item3후={i3p:.2f} diff={exclp-i3p:.2f}")
        print(f"      INCL(min(47-49,48)+49)={inclp:.2f} vs item3후={i3p:.2f} diff={inclp-i3p:.2f}")
        print(f"      EXCL+item54={exclp54:.2f} vs item3후={i3p:.2f} diff={exclp54-i3p:.2f}")
