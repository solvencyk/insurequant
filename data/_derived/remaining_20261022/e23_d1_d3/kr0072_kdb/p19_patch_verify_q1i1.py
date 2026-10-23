# -*- coding: utf-8 -*-
"""patch kr0072_verify.py: control of the old-layout item 1: Q1 live 7,111.35 = round(original item 2 - original item 16 (both unrounded), 2); Q2 live 22,665 = original item 2 (기타사업비용 not deducted: a different definition than Q1/Q3/Q4 -- reported)."""
from pathlib import Path

p = Path(__file__).resolve().parent / "kr0072_verify.py"
s = p.read_text(encoding="utf-8")
a = '''        lv1, lv2 = LIVE[(CODE, 1, q)]["값"], LIVE[(CODE, 2, q)]["값"]
        say(f"     i 1: live {lv1:,.2f} | original statement has no 보험손익 row; item 2 (live) {lv2:,.2f}, item 16 {oi[16]:,.2f} -> "
            + ("item 1 = item 2 - item 16 (Q1)" if q == "2023.1Q" and abs(lv1 - (lv2 - oi[16])) <= 0.0051 else ("item 1 = item 2 (Q2: the live value does not deduct 기타사업비용)" if abs(lv1 - lv2) <= 1e-6 else "UNEXPLAINED")))'''
b = '''        lv1, lv2 = LIVE[(CODE, 1, q)]["값"], LIVE[(CODE, 2, q)]["값"]
        expl = ("item 1 = original item 2 - original item 16 (rounded to 2 decimals), the standard definition" if q == "2023.1Q" and abs(lv1 - (oi[2] - oi[16])) <= 0.0051
                else ("item 1 = original item 2 (기타사업비용 NOT deducted: a different definition than 2023.1Q/3Q/4Q, where item 1 = item 2 - item 16; "
                      f"on the standard definition the live value would be {oi[2] - oi[16]:,.3f})" if q == "2023.2Q" and abs(lv1 - oi[2]) <= 0.5 + 1e-6 else "UNEXPLAINED"))
        say(f"     i 1: live {lv1:,.2f} | the original statement has no 보험손익 row; original item 2 {oi[2]:,.3f}, original item 16 {oi[16]:,.3f} -> {expl}")
        if expl == "UNEXPLAINED":
            ctrl_bad += 1
            problem(f"control {q} i1", "live item 1 is not explained by the original statement")'''
assert s.count(a) == 1
s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
