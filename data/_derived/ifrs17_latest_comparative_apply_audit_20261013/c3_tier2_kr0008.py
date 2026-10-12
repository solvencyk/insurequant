import sys, os, csv, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_tier2 import *
here = os.path.dirname(os.path.abspath(__file__))
code = "KR0008"
nts = note_tables(find_xml(code, "FY2024_Q1", "20240516001321")[0])
out = open(here + "/c3_tier2_kr0008.txt", "w", encoding="utf-8")
out.write(f"{len(nts)} note tables: {[(n['idx'], n['line'], len(n['rows'])) for n in nts]}\n")
for ty in pairs(nts): out.write(f"  pair {ty[0]['idx']} / {ty[1]['idx'] if ty[1] else None} sig={ty[0]['order'][:2]}\n")
