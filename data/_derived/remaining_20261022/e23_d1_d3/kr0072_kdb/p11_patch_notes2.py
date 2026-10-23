# -*- coding: utf-8 -*-
"""patch kdb_notes.py: (a) pl4_note accepts the original-layout table (no '합계' row; label '보험서비스수익 합계') and a `which` selector; (b) the CSM closing-row regex also takes 분기말/반기말/기말 without a prefix."""
from pathlib import Path

p = Path(__file__).resolve().parent / "kdb_notes.py"
s = p.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:80])
    s = s.replace(a, b)


sub('def pl4_note(rel):', 'def pl4_note(rel, which="prior"):')
sub('''        if want in labs and nspace("1. 보험영업수익") in labs and nspace("2. 재보험영업수익") in labs and "합계" in labs:''',
    '''        if want in labs and nspace("1. 보험영업수익") in labs and nspace("2. 재보험영업수익") in labs and ("합계" in labs or "보험서비스수익합계" in labs):''')
sub('''    nums = numeric_cells(row)
    t, ln, v = nums[-1]
    out = dict(printed=t,''', '''    nums = numeric_cells(row)
    if which == "prior":
        t, ln, v = nums[-1]
    elif which == "cur":      # cumulative of the CURRENT period: 2nd of 4 numerics (3개월 / 누적 pairs) or the 1st of 2
        t, ln, v = nums[1] if len(nums) == 4 else nums[0]
    else:
        raise ValueError(which)
    out = dict(printed=t,''')
sub('''re.match(r"^9\.(당분기말|당반기말|당기말|전분기말|전반기말|전기말)보험계약자산및부채", c) is not None''',
    '''re.match(r"^9\.(당분기말|당반기말|당기말|전분기말|전반기말|전기말|분기말|반기말|기말)보험계약자산및부채", c) is not None''')
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
