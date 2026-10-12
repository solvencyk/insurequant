# -*- coding: utf-8 -*-
p = "C:/Users/sangwook.cho/Desktop/insurequant/scripts/extract_amort_split_tables_20261012.py"
s = open(p, encoding="utf-8", newline="").read()
a = '    am = json.loads((ROOT / "CSM_amortization.json").read_bytes().decode("utf-8"))\n'
b = ('    # idempotent: once scripts/load_amort_split_tables_20261012.py has run, the "old" cells are the PRE-APPLY bytes it backed up\n'
     '    bk = ROOT / "data" / "_derived" / "ifrs17_owner_followups_backup_20261012" / "CSM_amortization.json.pre_amort_split"\n'
     '    am = json.loads((bk if bk.exists() else ROOT / "CSM_amortization.json").read_bytes().decode("utf-8"))\n')
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s)
print("patched")
