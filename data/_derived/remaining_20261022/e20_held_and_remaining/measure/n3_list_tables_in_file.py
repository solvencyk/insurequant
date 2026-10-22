"""n3: list tables (start line, caption, nrows, first header cells) of ONE xml file chosen by name suffix (e.g. _00760.xml) with a header filter.
usage: n3_list_tables_in_file.py <code> <FY_Q> <name_suffix> <header_substr[,..]> [min_rows]   (READ-ONLY)"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

sys.stdout.reconfigure(encoding="utf-8")
code, fy, suffix = sys.argv[1], sys.argv[2], sys.argv[3]
subs = [s for s in sys.argv[4].split(",") if s]
minr = int(sys.argv[5]) if len(sys.argv) > 5 else 10
path = [p for p in M.main_xmls(code, fy) if p.name.endswith(suffix)][0]
lines = M.read_lines(path)
print("#####", M.rel(path), len(lines))
for t in M.iter_tables(lines):
    hdr = " ".join(c["text"] for r in t["rows"][:6] for c in r["cells"])
    if len(t["rows"]) >= minr and all(s in hdr for s in subs):
        print(f"L{t['start']}-L{t['end']} cap[{t['caption_line']}]={t['caption'][:60]!r} nrows={len(t['rows'])} hdr={hdr[:110]!r}")
