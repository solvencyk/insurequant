# -*- coding: utf-8 -*-
p = "c04_diff_files.py"
s = open(p, encoding="utf-8").read()
a = 'chk(all(go[k] == gn[k] for k in go), "user_csm_cells.json: every old key\'s content identical (set, exclude_companies, _doc*)")'
b = '''chk(all(go[k] == gn[k] for k in go if k != "_doc"), "user_csm_cells.json: every old key's content identical (set, exclude_companies, _doc_e23_*)")
chk(gn["_doc"].startswith(go["_doc"]) and "null_dangi.cells" in gn["_doc"][len(go["_doc"]):], "user_csm_cells.json: the top-level _doc only gained the appended null_dangi sentence")'''
assert s.count(a) == 1
open(p, "w", encoding="utf-8", newline="\n").write(s.replace(a, b))
print("ok")
