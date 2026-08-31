# -*- coding: utf-8 -*-
"""Comprehensive identity verification for the 6 target companies against the
SCRATCH master (pre-live-apply), using the REAL rules engine's MARKET_M/R7
(never retyped) so the check is against the actual gate logic."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\src")
from pathlib import Path
from solvency.validation.kics_json_rules import MARKET_M, R7
import numpy as np

SCRATCH = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\scratch_master_final.json")
rows = json.loads(SCRATCH.read_text(encoding="utf-8"))
CODES = ["KR0069", "KR0070", "KR0082", "KR0001", "KR0073", "KR1011"]
Q = "2026.2Q"


def to_f(v):
    if v in (None, "", "None"):
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


for code in CODES:
    d = {int(r["항목번호"]): r for r in rows if r["원보험사코드"] == code and r["공시분기"] == Q and str(r["항목번호"]).isdigit()}
    items = sorted(d.keys())
    print(f"\n===== {code} {Q}: {len(items)} items in 1-46 range = {[i for i in items if i<=46]} =====")

    def v(i):
        return to_f(d[i]["값"]) if i in d else None

    # rule1: item1 = item2+item3
    a, b, c = v(1), v(2), v(3)
    if a is not None and b is not None and c is not None:
        print(f"  R1 item1=item2+item3: {a} vs {b}+{c}={b+c}  diff={a-(b+c):.2f}")

    # rule2: item4 = sum(5..11)
    a = v(4)
    comp = [v(i) for i in range(5, 12)]
    if a is not None and all(x is not None for x in comp):
        s = sum(comp)
        print(f"  R2 item4=Σ(5-11): {a} vs {s}  diff={a-s:.2f}")

    # rule5: item14 = 15-22+23
    a, i15, i22, i23 = v(14), v(15), v(22), v(23)
    if a is not None and i15 is not None and i22 is not None and i23 is not None:
        s = i15 - i22 + i23
        print(f"  R5 item14=15-22+23: {a} vs {s}  diff={a-s:.2f}")

    # rule7: item27 = item1/item14*100
    a, i1, i14 = v(27), v(1), v(14)
    if a is not None and i1 is not None and i14:
        s = i1 / i14 * 100
        print(f"  R7(27) item27=1/14*100: {a} vs {s:.4f}  diff={a-s:.4f}")

    # 8_life: item17 = sqrt(S'R7 S), S=[29-35]
    i17 = v(17)
    S = [v(i) for i in range(29, 36)]
    if i17 is not None and all(x is not None for x in S):
        Sarr = np.array(S)
        est = float(np.sqrt(max(Sarr @ R7 @ Sarr, 0)))
        rel = abs(est - i17) / i17 * 100 if i17 else None
        print(f"  8_life item17=sqrt(S'R7S): disclosed={i17} est={est:.2f}  rel={rel:.3f}%" if rel is not None else f"  8_life item17={i17} est={est:.2f}")
    else:
        print(f"  8_life: item17={i17} S(29-35)={S}  -- incomplete, skip")

    # 19_market: item19 = sqrt(V'MARKET_M V), V=[36-40]
    i19 = v(19)
    V = [v(i) for i in range(36, 41)]
    if i19 is not None and all(x is not None for x in V):
        Varr = np.array(V)
        est = float(np.sqrt(max(Varr @ MARKET_M @ Varr, 0)))
        rel = abs(est - i19) / i19 * 100 if i19 else None
        print(f"  19_market item19=sqrt(V'MARKET_M V): disclosed={i19} V={V} est={est:.2f}  rel={rel:.3f}%")
    else:
        print(f"  19_market: item19={i19} V(36-40)={V}  -- incomplete, skip")

    # 36_irr: item36 = sqrt(max(up,down)^2+max(flat,steep)^2)+mr, R=base-scenario 41-46
    i36 = v(36)
    IRR = [v(i) for i in range(41, 47)]
    if i36 is not None and all(x is not None for x in IRR):
        base, mr, up, down, flat, steep = IRR
        R_mr = base - mr
        R_up = max(base - up, 0.0)
        R_down = max(base - down, 0.0)
        R_flat = max(base - flat, 0.0)
        R_steep = max(base - steep, 0.0)
        est = (max(R_up, R_down) ** 2 + max(R_flat, R_steep) ** 2) ** 0.5 + R_mr
        rel = abs(est - i36) / i36 * 100 if i36 else None
        print(f"  36_irr item36=derive(41-46): disclosed={i36} est={est:.2f}  rel={rel:.3f}%")
    else:
        print(f"  36_irr: item36={i36} IRR(41-46)={IRR}  -- incomplete, skip")
