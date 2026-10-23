# -*- coding: utf-8 -*-
"""patch kr0072_verify.py: (1) the seam test only covers item-quarters the load touches (the item changes in the quarter or in the previous quarter), (2) D2 matches renamed rows by value and treats zero rows of obsolete labels as absent."""
from pathlib import Path

p = Path(__file__).resolve().parent / "kr0072_verify.py"
s = p.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:80])
    s = s.replace(a, b)


sub('''            cur, prev = after(q, item), after(prevq, item)
            if cur is None or prev is None:
                continue''', '''            if (q, item) not in plan_pl and (prevq, item) not in plan_pl:
                continue          # neither cumulative changes in this load -> the single quarter is untouched
            cur, prev = after(q, item), after(prevq, item)
            if cur is None or prev is None:
                continue''')
sub('''    n_match, unmatched = 0, []
    for lab, val, ln in n4c:
        cands = [lab] + ([shift[lab]] if lab in shift else [])
        hit = next((x for x in pool if x[0] in cands and abs(x[1] - val) <= 1e-9), None)
        if hit is None:
            unmatched.append((lab, val, ln))
        else:
            pool.remove(hit)
            n_match += 1
    say(f"    FY2024 annual prior column rows {len(n4c)} | matched in the FY2025 annual third column (same label or the shifted label, same value to the won) {n_match} | unmatched {len(unmatched)}")
    for u in unmatched[:12]:
        say(f"      unmatched: {u}")''', '''    n_match, n_renamed, n_zero_gone, unmatched = 0, 0, 0, []
    rest = []
    for lab, val, ln in n4c:
        cands = [lab] + ([shift[lab]] if lab in shift else [])
        hit = next((x for x in pool if x[0] in cands and abs(x[1] - val) <= 1e-9), None)
        if hit is None:
            rest.append((lab, val, ln))
        else:
            pool.remove(hit)
            n_match += 1
    for lab, val, ln in rest:
        hit = next((x for x in pool if abs(x[1] - val) <= 1e-9 and val != 0.0), None)
        if hit is not None:
            pool.remove(hit)
            n_renamed += 1
            say(f"      renamed row (same value to the won): FY2024 annual L{ln} '{lab}' {val:,.0f} == FY2025 annual L{hit[2]} '{hit[0]}'")
        elif val == 0.0:
            n_zero_gone += 1
        else:
            unmatched.append((lab, val, ln))
    say(f"    FY2024 annual prior column rows {len(n4c)} | same label (or shifted label) and same value to the won {n_match} | renamed row with the same value {n_renamed} | zero rows of obsolete labels not reprinted {n_zero_gone} | NOT reproduced {len(unmatched)}")
    for u in unmatched[:12]:
        say(f"      NOT reproduced: {u}")''')
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
