import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
fy, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
path = [p for p in M.main_xmls("KR0003", fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
lines = M.read_lines(path)
for t in M.iter_tables(lines):
    if lo <= t["start"] <= hi:
        r0 = " ".join(c["text"] for c in t["rows"][0]["cells"])[:90] if t["rows"] else ""
        nrow = len(t["rows"])
        print(f"L{t['start']}-L{t['end']} nrows={nrow} row0={r0!r}")
