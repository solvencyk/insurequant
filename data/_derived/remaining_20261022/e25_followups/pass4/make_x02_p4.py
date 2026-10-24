# -*- coding: utf-8 -*-
"""Generate x02_diff_files_p4.py from the audited pass3 diff checker (pass3/x02_diff_files_p3.py) with asserted substitutions (pass4 plan, _doc_p4 key, note-only appends of existing gold entries)."""
from pathlib import Path
SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/x02_diff_files_p3.py")
DST = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/x02_diff_files_p4.py")
s = SRC.read_text(encoding="utf-8")
def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90])
    s = s.replace(old, new)
rep('EV = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3"', 'EV = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4"')
rep('plan = json.load(open(f"{EV}/p3_plan.json", encoding="utf-8"))', 'plan = json.load(open(f"{EV}/p4_plan.json", encoding="utf-8"))')
rep('extra_doc = {"_doc_p3_20261024"} if kk == "null_dangi" else set()', 'extra_doc = {"_doc_p4_20261024"} if kk == "null_dangi" else set()')
rep('rep = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_replace"]}\n', 'rep = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_replace"]}\nnapp = {(e["code"], e["item"], e["quarter"]): e for e in C.get("gold_note_append", [])}\n')
rep('''    else:
        same_prefix &= (a == b)
chk(same_prefix, "user_pl_cells.json: every old entry unchanged except the planned in-place replacement(s)")''', '''    elif k in napp:
        same_prefix &= (b["note"] == a["note"] + napp[k]["append"] and all(b[f] == a[f] for f in a if f != "note"))
    else:
        same_prefix &= (a == b)
chk(same_prefix, f"user_pl_cells.json: every old entry unchanged except the {len(rep)} planned in-place replacement(s) and the {len(napp)} planned note-only append(s) (value untouched)")''')
DST.write_text(s, encoding="utf-8", newline="\n")
print("written", DST)
