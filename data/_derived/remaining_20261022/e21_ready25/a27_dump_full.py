"""a27_dump_full: SPAN-aware dump of one note table (e21_raw.rows_full) by start line (READ-ONLY).
usage: a27_dump_full.py <code> <FY_Q> <start_line> [maxcols=14]"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_raw as W  # noqa: E402
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
        for r in W.rows_full(lines, t["start"], t["end"]):
            print(f"  R{r['tr_line']}: " + " | ".join((c["text"][:40] + (f"@{c['line']}" if k else "")) for k, c in enumerate(r["cells"][:maxc])))
        break
else:
    print("table not found")
