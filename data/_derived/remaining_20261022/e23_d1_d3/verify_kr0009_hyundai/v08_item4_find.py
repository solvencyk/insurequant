import sys
sys.path.insert(0, ".")
import vlib9
out = open("v08_item4_find.txt", "w", encoding="utf-8")
for fy in ("FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"):
    lines = vlib9.load(fy)
    sec = [i for i, ln in enumerate(lines, 1) if "<TITLE" in ln and "5. 재무제표 주석" in ln][0]
    T = vlib9.tables(fy)
    out.write("== %s sec %d\n" % (fy, sec))
    for ti, t in enumerate(T):
        if t["start"] < sec: continue
        for r in t["rows"]:
            cs = r["cells"]
            if cs and "마진" in cs[0][1] and "상각" in cs[0][1]:
                hdr = [c[1][:14] for c in t["rows"][0]["cells"]] + [c[1][:14] for c in t["rows"][1]["cells"]] if len(t["rows"]) > 1 else []
                out.write("table %d (%d-%d) hdr %s\n  [%d] %s\n" % (ti, t["start"], t["end"], hdr, r["line"], [c[1] for c in cs]))
out.close()
