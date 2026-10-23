# -*- coding: utf-8 -*-
from pathlib import Path
p = Path(__file__).resolve().parent / "kr0009_diff_vs_backup.py"
s = p.read_text(encoding="utf-8")
a = 'chk("CSM gold: the replaced entry kept `was` and its old why verbatim inside the new why, with the owner approval", all(e["old_entry"]["why"] in e["why"] and "owner 2026-10-23 승인" in e["why"] and lcg["set"][[gk(x) for x in kept].index((e["code"], e["item"], e["quarter"]))]["was"] == e["old_entry"]["was"] for e in C["csm_gold_replace"]))'
b = 'chk("CSM gold: the replaced entry `was` = the previous gold value (chain convention, e21/ABL/KDB), and its why holds the old why verbatim, the old `was` and the owner approval", all(e["old_entry"]["why"] in e["why"] and f"이전 was {e[\'old_entry\'][\'was\']}" in e["why"] and "owner 2026-10-23 승인" in e["why"] and lcg["set"][[gk(x) for x in kept].index((e["code"], e["item"], e["quarter"]))]["was"] == e["old_entry"]["값"] for e in C["csm_gold_replace"]))'
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
