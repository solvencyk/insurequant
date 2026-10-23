# -*- coding: utf-8 -*-
p = "x01_verify_e25.py"
s = open(p, encoding="utf-8").read()

def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)

# (1) seam bookkeeping: keep cumulative vectors per quarter
rep('''    prev = {}
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):''', '''    cum_by_q = {}
    PREV_Q = {"2023.2Q": "2023.1Q", "2023.3Q": "2023.2Q", "2023.4Q": "2023.3Q"}
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):''')
rep('''            pr = prev[q]
''', '''            pr = cum_by_q[PREV_Q[q]]
''')
rep('''        prev_q = {"2023.2Q": "2023.1Q", "2023.3Q": "2023.2Q", "2023.4Q": "2023.3Q"}.get(q)
        prev[{"2023.1Q": "2023.2Q", "2023.2Q": "2023.3Q", "2023.3Q": "2023.4Q"}.get(q, "x")] = {4: csm, 5: ra, 6: v6, 9: v9, 10: v10}
''', '''        cum_by_q[q] = {4: csm, 5: ra, 6: v6, 9: v9, 10: v10}
''')
# (7) mutation 'line' must move the cited cell lines
rep('''            ln = key[2][(key[0], key[1])][col]
            r = read_cell(rel, ln)''', '''            ln = mut_line(key[2][(key[0], key[1])][col])
            r = read_cell(rel, ln)''')
rep('''rv, rc, ru = parse_note_table(rel, rec["rev_table"] + (1 if MUT == "line" else 0))''', '''rv, rc, ru = parse_note_table(rel, rec["rev_table"])''')
# stray expression
rep('''  (재분류 {vals[17] - live[17] if False else ''})")''', '''")''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
