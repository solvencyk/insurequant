# -*- coding: utf-8 -*-
import json, difflib, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
a = json.load(open(ROOT + "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0003_lotte/extra/tests/fixtures/master_tables_golden.json", encoding="utf-8"))
b = json.load(open(ROOT + "tests/fixtures/master_tables_golden.json", encoding="utf-8"))
print("keys", list(a), list(b))
print("exit_code", a["exit_code"], "->", b["exit_code"])
sa, sb = a["summary"].split(" | "), b["summary"].split(" | ")
print("fields", len(sa), len(sb))
for x, y in zip(sa, sb):
    if x != y:
        print("  CHANGED:", x, "=>", y)
print("other keys equal:", all(a[k] == b[k] for k in a if k != "summary"))
