import sys, re
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl")
import vlib
for fy in ("FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"):
    print("=====", fy)
    for t in vlib.tables(fy):
        for r in t["rows"]:
            lab = r["cells"][0][1] if r["cells"] else ""
            if ("보험계약마진" in lab and "상각" in lab) or ("제공된 서비스" in lab and "당기손익" in lab) or lab.replace(" ", "").startswith("보험계약마진상각"):
                hdr = [c[1][:30] for c in t["rows"][0]["cells"]] if t["rows"] else []
                hdr2 = [c[1][:20] for c in t["rows"][1]["cells"]] if len(t["rows"]) > 1 else []
                print("T%d-%d L%d | %s | hdr %s / %s" % (t["start"], t["end"], r["line"], " | ".join(c[1][:40] for c in r["cells"]), hdr, hdr2))
