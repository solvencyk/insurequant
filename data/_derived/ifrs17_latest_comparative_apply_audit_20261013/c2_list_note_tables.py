import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_dart import *
here = os.path.dirname(os.path.abspath(__file__))
code, fyq, rc = sys.argv[1].split(":")
pat = sys.argv[2]
p = find_xml(code, fyq, rc)[0]
tabs = load_tables(p)
out = open(here + "/c2_list_note_tables.txt", "w", encoding="utf-8")
for t in tabs:
    flat = " ".join(" ".join(r) for r in t["rows"])
    if re.search(pat, flat):
        h = " | ".join(t["rows"][0])[:100] if t["rows"] else ""
        out.write(f"table {t['idx']} line {t['line']} rows={len(t['rows'])} hdr={h} cap={t['caption'][:80]!r} first={[r[0][:20] for r in t['rows'][1:4]]}\n")
