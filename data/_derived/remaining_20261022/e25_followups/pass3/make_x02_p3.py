# -*- coding: utf-8 -*-
"""Generate x02_diff_files_p3.py from the audited pass2 diff checker (pass2/x02_diff_files_p2.py) with asserted substitutions (pass3 plan, null_dangi removals, the _doc_p3 key)."""
from pathlib import Path
SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2/x02_diff_files_p2.py")
DST = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/x02_diff_files_p3.py")
s = SRC.read_text(encoding="utf-8")
def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90])
    s = s.replace(old, new)
rep('EV = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2"', 'EV = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3"')
rep('plan = json.load(open(f"{EV}/p2_plan.json", encoding="utf-8"))', 'plan = json.load(open(f"{EV}/p3_plan.json", encoding="utf-8"))')
rep('''for kk, add in (("null_dangi", C["null_dangi_add"]), ("set_dangi", C["set_dangi_add"])):
    chk({a: b for a, b in go[kk].items() if a != "cells"} == {a: b for a, b in gn[kk].items() if a != "cells"}, f"user_pl_cells.json: '{kk}' non-cell keys identical")
    chk(gn[kk]["cells"] == go[kk]["cells"] + [list(x) for x in add], f"user_pl_cells.json: '{kk}' cells = old {len(go[kk]['cells'])} + planned {len(add)} appended in plan order")''',
'''REMOVED = {tuple(x) for x in C["null_dangi_remove"]}
for kk, add, rem in (("null_dangi", C["null_dangi_add"], REMOVED), ("set_dangi", C["set_dangi_add"], set())):
    extra_doc = {"_doc_p3_20261024"} if kk == "null_dangi" else set()
    chk({a: b for a, b in go[kk].items() if a != "cells"} == {a: b for a, b in gn[kk].items() if a != "cells" and a not in extra_doc} and set(gn[kk]) - set(go[kk]) == extra_doc,
        f"user_pl_cells.json: '{kk}' non-cell keys identical" + (f" except the new {sorted(extra_doc)}" if extra_doc else ""))
    exp_cells = [x for x in go[kk]["cells"] if (x[0], x[1], int(x[2])) not in rem] + [list(x) for x in add]
    chk(gn[kk]["cells"] == exp_cells, f"user_pl_cells.json: '{kk}' cells = old {len(go[kk]['cells'])} - {len(rem)} removed + {len(add)} appended in plan order")''')
DST.write_text(s, encoding="utf-8", newline="\n")
print("written", DST)
