# -*- coding: utf-8 -*-
"""c6: 코리안리 (KR1000) - what does the issuer's own 공통적용 경과조치 step say about how it treats its hybrids?

Step_t = item2 값_적용후 - item2 값  (기본자본 added by the common transitional measure, 억원).  Reference amounts per quarter:
    L_t       = item 53 (기발행 신종)
    cap10_t   = 10% x item14(값), cap15_t = 15% x item14(값), five_t = 5% x item14(값)
Readings of the step:
    step == five_t    : hybrids form ONE basic-type pool larger than the 15% cap in both worlds (pre-world 10% cap, post-world 15% cap) - everything counted as basic-type
    step == L_t       : legacy hybrids are tier2-type in the pre-world and become basic (below 15%) after the step, new hybrids are tier2-type OR sit in a separate 10% bucket
    step == 0 (pre = post printed)  : the headline already carries the common step (item 13 on the post basis)
Also prints X = item13 - item49, X on the pre basis (item3 pre - item49) and the joint-15%-pool fit  max(0, L + new - cap15).
Read-only; pinned only for the master (kics_disclosure.json).   Output c6_koreanre_tfi_step.txt
"""
import json

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
QS = ["%d.%dQ" % (y, n) for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
code = "KR1000"


def num(x):
    try:
        return float(str(x).replace(",", ""))
    except Exception:
        return None


kd = json.load(open(ROOT + "/kics_disclosure.json", encoding="utf-8"))
S = {}
for r in kd:
    if r["원보험사코드"] == code and r["항목번호"] in (2, 3, 6, 13, 14, 49, 53):
        S.setdefault((r["항목번호"], "pre"), {})[r["공시분기"]] = num(r.get("값"))
        S.setdefault((r["항목번호"], "post"), {})[r["공시분기"]] = num(r.get("값_적용후"))
NEW = {"2023.1Q": 2500.0, "2024.4Q": 4800.0}      # new hybrids outstanding from the quarter on (제5회 2023-03, 제6회 2024-10), tier2 per registry
L = ["quarter | step(i2post-i2pre) | 5%S | L53 | step==5%S? | step==L? | X=13-49 | X_pre=3pre-49 | joint15 overflow max(0,L+new-15%S) | X - joint15"]
new_now = 0.0
for q in QS:
    if q == "2023.1Q":
        new_now = 2500.0
    if q == "2024.4Q":
        new_now = 4800.0
    g = lambda it, c="pre": S.get((it, c), {}).get(q)
    s14 = g(14)
    i2p, i2q = g(2), g(2, "post")
    step = None if (i2p is None or i2q is None) else i2q - i2p
    five = 0.05 * s14
    l53 = g(53) or 0.0
    x = None if (g(13) is None or g(49) is None) else g(13) - g(49)
    xp = None if (g(3) is None or g(49) is None) else g(3) - g(49)
    joint = max(0.0, l53 + new_now - 0.15 * s14)
    L.append("%s | %s | %.1f | %.1f | %s | %s | %s | %s | %.1f | %s" % (
        q, "None" if step is None else "%.1f" % step, five, l53,
        "YES" if (step is not None and abs(step - five) <= max(2.0, 0.01 * five)) else "no",
        "YES" if (step is not None and l53 > 0 and abs(step - l53) <= max(2.0, 0.01 * l53)) else "no",
        "None" if x is None else "%.1f" % x, "None" if xp is None else "%.1f" % xp, joint,
        "None" if x is None else "%.1f" % (x - joint)))
L.append("")
L.append("reading: step == 5% x SCR in 2023.1Q and 2024.4Q  => in those quarters the issuer's table is consistent with ALL hybrids in one basic-type pool above the caps;")
L.append("         step == item 53 from 2025.1Q on => consistent with tier2-type new hybrids (or separate buckets); X - joint15 ~ 0 (+-5) for 2023.2Q-2024.3Q fits BOTH 'new = tier2 inside X' and 'one pooled 15% cap'.")
open(HERE + "c6_koreanre_tfi_step.txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
