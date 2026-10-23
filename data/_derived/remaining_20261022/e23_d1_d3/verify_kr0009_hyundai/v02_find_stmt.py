import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0009_hyundai")
import vlib9
fy = sys.argv[1]
key = sys.argv[2]
out = open(sys.argv[3], "w", encoding="utf-8")
T = vlib9.tables(fy)
out.write("%s tables=%d\n" % (fy, len(T)))
lines = vlib9.load(fy)
for ti, t in enumerate(T):
    labs = [r["cells"][0][1] if r["cells"] else "" for r in t["rows"]]
    if any(key in l for l in labs):
        # heading: look back up to 12 lines for text
        head = []
        for j in range(max(0, t["start"] - 14), t["start"] - 1):
            s = lines[j].strip()
            if s and "TABLE" not in s:
                head.append(s[:110])
        out.write("\n#### table %d lines %d-%d rows=%d\n" % (ti, t["start"], t["end"], len(t["rows"])))
        out.write("  ctx: %s\n" % " | ".join(head[-3:]))
        for r in t["rows"][:8]:
            out.write("  [%d] %s\n" % (r["line"], [c[1][:30] for c in r["cells"]]))
out.close()
