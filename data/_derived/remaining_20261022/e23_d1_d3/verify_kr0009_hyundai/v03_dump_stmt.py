import sys, re
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0009_hyundai")
import vlib9

def sep_stmt(fy, title_pat="포괄손익계산서"):
    """separate (non-consolidated) comprehensive income statement: table following a <TITLE> that has
    title_pat but not 연결. returns (table, title_line)"""
    lines = vlib9.load(fy)
    T = vlib9.tables(fy)
    tl = []
    for i, ln in enumerate(lines, 1):
        if "<TITLE" in ln and title_pat in ln and "연결" not in ln:
            tl.append(i)
    res = []
    for ti in tl:
        for t in T:
            if t["start"] > ti:
                labs = [r["cells"][0][1] if r["cells"] else "" for r in t["rows"]]
                if "보험손익" in labs or any(l.startswith("보험손익") for l in labs):
                    res.append((t, ti)); break
    return res

if __name__ == "__main__":
    fy = sys.argv[1]
    out = open(sys.argv[2], "w", encoding="utf-8")
    r = sep_stmt(fy)
    out.write("%s found=%d\n" % (fy, len(r)))
    for t, ti in r:
        out.write("title line %d, table lines %d-%d rows=%d\n" % (ti, t["start"], t["end"], len(t["rows"])))
        for row in t["rows"]:
            out.write("[%d] %s\n" % (row["line"], [c[1] for c in row["cells"]]))
    out.close()
