"""a23_dump_table: dump one note table of a filing by its start line (rows: label | cells with physical line numbers) to stdout (READ-ONLY).
usage: a23_dump_table.py <code> <FY_Q> <start_line> [maxcols=14] [file_suffix_filter]"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_t2 as T  # noqa: E402

M = T.M
sys.stdout.reconfigure(encoding="utf-8")
code, fy, start = sys.argv[1], sys.argv[2], int(sys.argv[3])
maxc = int(sys.argv[4]) if len(sys.argv) > 4 else 14
path = T.main_path(code, fy)
lines = M.read_lines(path)
print("#####", M.rel(path))
for t in M.iter_tables(lines):
    if t["start"] == start:
        print(f"TABLE L{t['start']}-L{t['end']} caption[{t['caption_line']}]={t['caption'][:120]!r}")
        for r in t["rows"]:
            print(f"  R{r['tr_line']}: " + " | ".join((c["text"][:34] + (f"@{c['line']}" if k else "")) for k, c in enumerate(r["cells"][:maxc])))
        break
else:
    print("table not found")
