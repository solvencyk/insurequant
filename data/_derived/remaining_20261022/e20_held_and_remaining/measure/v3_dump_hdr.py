import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
code, fy, start = sys.argv[1], sys.argv[2], int(sys.argv[3])
path = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
lines = M.read_lines(path)
for t in M.iter_tables(lines):
    if t["start"] == start:
        print("rows", len(t["rows"]))
        for r in t["rows"][:8]:
            print("R%d ncells=%d: " % (r["tr_line"], len(r["cells"])) + " | ".join(f"{c['text'][:18]}(cs{c['colspan']})" for c in r["cells"][:60]))
        for r in t["rows"]:
            lab = r["cells"][0]["text"] if r["cells"] else ""
            print("R%d n=%d %s | %s" % (r["tr_line"], len(r["cells"]), lab[:30], " ".join(c["text"][:16] for c in r["cells"][1:4])))
        break
