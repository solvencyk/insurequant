# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / "c13_emitter_prestate.py"
s = p.read_text(encoding="utf-8")
a = '''for tag, base in (("PRE-LOAD (backup)", BK), ("POST-LOAD (repo)", ROOT)):'''
b = '''SIM = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e23_kr0072_sim")   # byte-identical to what --apply wrote (c18_sim_vs_applied.txt)
for tag, base in (("PRE-LOAD (backup)", BK), ("POST-LOAD (simulation = applied)", SIM)):'''
assert s.count(a) == 1
s = s.replace(a, b)
s = s.replace('tag.split()[0].lower().replace("-", "")', 'tag.split()[0].lower().replace("-", "")')
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
