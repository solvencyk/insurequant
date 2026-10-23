# -*- coding: utf-8 -*-
"""Generate x02_diff_files_p2.py from the audited e25 diff checker (x02_diff_files.py) with asserted substitutions."""
from pathlib import Path

SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/x02_diff_files.py")
DST = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2/x02_diff_files_p2.py")
s = SRC.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep('EV = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups"', 'EV = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2"')
rep('plan = json.load(open(f"{EV}/e25_plan.json", encoding="utf-8"))', 'plan = json.load(open(f"{EV}/p2_plan.json", encoding="utf-8"))')
rep('''for kk in go:
    if kk != "set":
        chk(go[kk] == gn[kk], f"user_pl_cells.json: '{kk}' identical")''', '''for kk in go:
    if kk not in ("set", "null_dangi", "set_dangi"):
        chk(go[kk] == gn[kk], f"user_pl_cells.json: '{kk}' identical")
for kk, add in (("null_dangi", C["null_dangi_add"]), ("set_dangi", C["set_dangi_add"])):
    chk({a: b for a, b in go[kk].items() if a != "cells"} == {a: b for a, b in gn[kk].items() if a != "cells"}, f"user_pl_cells.json: '{kk}' non-cell keys identical")
    chk(gn[kk]["cells"] == go[kk]["cells"] + [list(x) for x in add], f"user_pl_cells.json: '{kk}' cells = old {len(go[kk]['cells'])} + planned {len(add)} appended in plan order")''')

rep("""bad = []
for k, (a, b) in chg_dangi.items():
    c, i, q = k
    cur = rowsN[k]["값"]
    pq = prev_q(q)
    exp = cur if pq is None else (None if (cur is None or rowsN.get((c, i, pq), {}).get("값") is None) else round(cur - rowsN[(c, i, pq)]["값"], 6))
""", """bad = []
SEAM_SET = {(x[0], x[2], x[1]): float(x[3]) for x in C["set_dangi_add"]}
SEAM_NULL = {(x[0], x[2], x[1]) for x in C["null_dangi_add"]}
for k, (a, b) in chg_dangi.items():
    c, i, q = k
    cur = rowsN[k]["값"]
    pq = prev_q(q)
    exp = cur if pq is None else (None if (cur is None or rowsN.get((c, i, pq), {}).get("값") is None) else round(cur - rowsN[(c, i, pq)]["값"], 6))
    if k in SEAM_SET:
        exp = SEAM_SET[k]
    elif k in SEAM_NULL:
        exp = None
""")
rep("""chk(not bad, f"PL_breakdown.json: every changed 값_당분기 equals cumulative - previous cumulative of the NEW master ({bad[:3]})")""",
    """chk(not bad, f"PL_breakdown.json: every changed 값_당분기 equals cumulative - previous cumulative of the NEW master, except the planned seam cells (set_dangi {len(SEAM_SET)} = printed 3M, null_dangi {len(SEAM_NULL)} = blank) ({bad[:3]})")
for k, v in SEAM_SET.items():
    chk(rowsN[k]["값_당분기"] is not None and abs(rowsN[k]["값_당분기"] - v) < 1e-6, f"seam set_dangi {k}: master 값_당분기 {rowsN[k]['값_당분기']} == planned {v}")
for k in SEAM_NULL:
    chk(rowsN[k]["값_당분기"] is None, f"seam null_dangi {k}: master 값_당분기 is blank")""")
DST.write_text(s, encoding="utf-8", newline="\n")
print("written", DST)
