"""n2: dump one table of a filing by its start line (rows: label | cells with line numbers) (READ-ONLY).
usage: n2_dump_table.py <code> <FY_Q> <start_line> [file_index=0] [maxcols=9]"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

sys.stdout.reconfigure(encoding="utf-8")
code, fy, start = sys.argv[1], sys.argv[2], int(sys.argv[3])
fi = int(sys.argv[4]) if len(sys.argv) > 4 else 0
maxc = int(sys.argv[5]) if len(sys.argv) > 5 else 9
sel = sys.argv[6] if len(sys.argv) > 6 else None
path = [p for p in M.main_xmls(code, fy) if (p.name.endswith(sel) if sel else not p.name.endswith(("_00760.xml", "_00761.xml")))][fi]
lines = M.read_lines(path)
out = [f"##### {M.rel(path)}"]
for t in M.iter_tables(lines):
    if t["start"] == start:
        out.append(f"TABLE L{t['start']}-L{t['end']} title={t['title'][:40]!r} caption[{t['caption_line']}]={t['caption'][:90]!r}")
        for r in t["rows"]:
            out.append(f"  R{r['tr_line']}: " + " | ".join((c["text"][:26] + (f"@{c['line']}" if k else "")) for k, c in enumerate(r["cells"][:maxc])))
        break
txt = "\n".join(out)
M.MEASURE.joinpath(f"n2_{code}_{fy}_{start}.txt").write_text(txt, encoding="utf-8")
print(txt)
