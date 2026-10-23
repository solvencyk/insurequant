# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / "c16_tax_collapse_candidates.py"
s = p.read_text(encoding="utf-8")
a = '''for tag, p in (("PRE-LOAD (backup)", BK / "PL_breakdown.json"), ("POST-LOAD (live)", ROOT / "PL_breakdown.json")):'''
b = '''SIM = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e23_kr0072_sim")   # byte-identical to what --apply wrote (c18_sim_vs_applied.txt)
for tag, p in (("PRE-LOAD (backup = reverted tree)", BK / "PL_breakdown.json"), ("POST-LOAD (--out-dir simulation = the applied masters)", SIM / "PL_breakdown.json")):'''
assert s.count(a) == 1
p.write_text(s.replace(a, b), encoding="utf-8", newline="\n")
print("patched")
