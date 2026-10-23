import sys
sys.path.insert(0, ".")
import vlib9
fy = sys.argv[1]
lines = vlib9.load(fy)
T = vlib9.tables(fy)
# separate-notes section start: TITLE '5. 재무제표 주석'
sec = None
for i, ln in enumerate(lines, 1):
    if "<TITLE" in ln and "5. 재무제표 주석" in ln: sec = i
out = open("v06_csm_tables_%s.txt" % fy, "w", encoding="utf-8")
out.write("%s separate-notes section starts line %s\n" % (fy, sec))
for ti, t in enumerate(T):
    labs = [r["cells"][0][1] if r["cells"] else "" for r in t["rows"]]
    if "기초순보험계약부채" in labs and t["start"] > (sec or 0):
        ctx = []
        for j in range(max(0, t["start"] - 40), t["start"] - 1):
            s = lines[j].strip()
            if s and ("<P" in s or "<TD" in s) and "TABLE" not in s:
                ctx.append(s[:100])
        out.write("\n#### table %d lines %d-%d rows=%d\n  ctx: %s\n" % (ti, t["start"], t["end"], len(t["rows"]), " | ".join(ctx[-4:])))
        for r in t["rows"]:
            out.write("  [%d] %s\n" % (r["line"], [c[1][:40] for c in r["cells"]]))
out.close()
