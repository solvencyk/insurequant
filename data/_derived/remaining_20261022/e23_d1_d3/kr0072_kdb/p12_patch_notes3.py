# -*- coding: utf-8 -*-
"""patch kdb_notes.py (cur_3m / cur_cum fields for 4-numeric tables) and kr0072_verify.py (the PL gold line for 2023.2Q prints both current columns)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def patch(fname, subs):
    p = HERE / fname
    s = p.read_text(encoding="utf-8")
    for a, b in subs:
        assert s.count(a) == 1, (fname, s.count(a), a[:80])
        s = s.replace(a, b)
    p.write_text(s, encoding="utf-8", newline="\n")


patch("kdb_notes.py", [(
    '''    if len(nums) == 4:
        t3, ln3, _ = nums[2]
        out["prior_3m"] = dict(printed=t3, line=ln3, mn=mn(t3, un))''',
    '''    if len(nums) == 4:
        t3, ln3, _ = nums[2]
        out["prior_3m"] = dict(printed=t3, line=ln3, mn=mn(t3, un))
        out["cur_3m"] = dict(printed=nums[0][0], line=nums[0][1], mn=mn(nums[0][0], un))
        out["cur_cum"] = dict(printed=nums[1][0], line=nums[1][1], mn=mn(nums[1][0], un))''')])
patch("kr0072_verify.py", [(
    '''            n3 = pl4_note(F["O2"], "cur")
            say(f"     i 4: live {LIVE[(CODE, 4, q)]['값']:,.1f} (owner gold) | original note (3) 제공된 서비스의 보험계약마진: 3개월 {n3['prior_3m']['printed'] if False else ''}cumulative {n3['printed']} (L{n3['line']})")''',
    '''            n3 = pl4_note(F["O2"], "cur")
            say(f"     i 4: live {LIVE[(CODE, 4, q)]['값']:,.1f} (owner gold) | original note (3) 제공된 서비스의 보험계약마진: 3개월 {n3['cur_3m']['printed']} (L{n3['cur_3m']['line']}) / 누적 {n3['cur_cum']['printed']} (L{n3['cur_cum']['line']}) -> the live value is the CUMULATIVE column (the pre-fix builder value 12,290 was the 3개월 column)")
            if abs(LIVE[(CODE, 4, q)]["값"] - n3["cur_cum"]["mn"]) > 0.5:
                ctrl_bad += 1
                problem("control 2023.2Q i4", "live item 4 is not the original cumulative column")''')])
print("patched")
