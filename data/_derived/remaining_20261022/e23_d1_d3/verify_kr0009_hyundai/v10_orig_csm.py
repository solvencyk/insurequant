import sys
sys.path.insert(0, ".")
import vlib9
out = open("v10_orig_csm.txt", "w", encoding="utf-8")
for fy in ("FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2023_Q4"):
    lines = vlib9.load(fy)
    secs = [i for i, ln in enumerate(lines, 1) if "<TITLE" in ln and "5. 재무제표 주석" in ln]
    sec = secs[0] if secs else 0
    T = vlib9.tables(fy)
    out.write("== %s sec %s tables %d\n" % (fy, sec, len(T)))
    for ti, t in enumerate(T):
        if t["start"] < sec: continue
        labs = [r["cells"][0][1] if r["cells"] else "" for r in t["rows"]]
        if "기초순보험계약부채" in labs and "보험계약마진" in [c[1] for c in t["rows"][0]["cells"]] and len(t["rows"]) >= 26:
            out.write("table %d lines %d-%d rows %d\n" % (ti, t["start"], t["end"], len(t["rows"])))
            for r in t["rows"]:
                cs = r["cells"]
                if cs and (cs[0][1] in ("기초순보험계약부채", "신계약효과", "보험금융손익", "보험계약마진을 조정하는 변동", "보험계약마진상각") or cs[0][1].endswith("말보험계약순부채")):
                    out.write("  [%d] %s CSM(천원)=%s\n" % (r["line"], cs[0][1], cs[3][1]))
out.close()
